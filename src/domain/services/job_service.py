from __future__ import annotations

import logging
from datetime import datetime, timedelta, UTC
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.models.job import Job, JobStatus

if TYPE_CHECKING:
    from src.infrastructure.slack_client import SlackClient

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class JobService:
    """ジョブの取得・ステータス管理・リトライ制御を担うサービス。"""

    def __init__(
        self,
        *,
        db: Session,
        max_concurrency: int,
        max_retry_count: int,
        retry_delay_seconds: int,
        slack_client: SlackClient | None,
    ) -> None:
        self._db = db
        self._max_concurrency = max_concurrency
        self._max_retry_count = max_retry_count
        self._retry_delay = retry_delay_seconds
        self._slack = slack_client

    def claim_pending_jobs(self, limit: int | None = None) -> list[Job]:
        """pending かつ retry_after が過去のジョブを取得し processing に変更する。

        Args:
            limit: 取得上限数。None の場合は max_concurrency を使用する。

        MySQL では SELECT FOR UPDATE SKIP LOCKED を使用して同時取得を防ぐ。
        SQLite（ユニットテスト用）では SKIP LOCKED をスキップする。
        """
        effective_limit = limit if limit is not None else self._max_concurrency
        now = _utcnow()
        stmt = (
            select(Job)
            .where(
                Job.status == JobStatus.pending,
                (Job.retry_after == None) | (Job.retry_after <= now),  # noqa: E711
            )
            .limit(effective_limit)
            .with_for_update(skip_locked=True)
        )
        try:
            jobs = list(self._db.scalars(stmt))
        except Exception:
            # SQLite など SKIP LOCKED 非対応 DB のフォールバック
            stmt_fallback = (
                select(Job)
                .where(
                    Job.status == JobStatus.pending,
                    (Job.retry_after == None) | (Job.retry_after <= now),  # noqa: E711
                )
                .limit(effective_limit)
            )
            jobs = list(self._db.scalars(stmt_fallback))

        for job in jobs:
            job.status = JobStatus.processing
        self._db.commit()
        return jobs

    def mark_done(self, job: Job) -> None:
        """ジョブを成功状態に遷移させる。"""
        job.status = JobStatus.done
        self._db.commit()

    def mark_failed(self, job: Job, reason: str) -> None:
        """ジョブを失敗として処理する。

        - リトライ上限以内 → pending に戻し retry_count++ / retry_after を設定
        - リトライ上限超過 → failed に設定し Slack に最終通知
        """
        job.failure_reason = reason

        if job.retry_count < self._max_retry_count:
            job.retry_count += 1
            job.status = JobStatus.pending
            job.retry_after = _utcnow() + timedelta(seconds=self._retry_delay)
            self._db.commit()
            logger.warning(
                "Job %d failed (%s). Retry %d/%d after %s.",
                job.id,
                reason,
                job.retry_count,
                self._max_retry_count,
                job.retry_after,
            )
        else:
            job.status = JobStatus.failed
            self._db.commit()
            logger.error("Job %d permanently failed: %s", job.id, reason)
            if self._slack is not None:
                ctx = job.thread_context
                self._slack.post_message(
                    channel=ctx.get("channel_id", ""),
                    thread_ts=ctx.get("thread_ts"),
                    text=f"エラー: コマンド `!{job.command}` が {self._max_retry_count} 回失敗しました。理由: {reason}",
                )

    def mark_failed_no_retry(self, job: Job, reason: str) -> None:
        """リトライなしで即座に failed にする。

        プラグインが NoRetryError を送出した場合に呼び出される。
        """
        job.failure_reason = reason
        job.status = JobStatus.failed
        self._db.commit()
        logger.error("Job %d failed without retry: %s", job.id, reason)
        if self._slack is not None:
            ctx = job.thread_context
            self._slack.post_message(
                channel=ctx.get("channel_id", ""),
                thread_ts=ctx.get("thread_ts"),
                text=f"エラー: `!{job.command}` が失敗しました。{reason}",
            )
