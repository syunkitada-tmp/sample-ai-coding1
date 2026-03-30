import json
import pytest
from datetime import datetime, timedelta, UTC

from src.domain.models.job import Job, JobStatus


def _utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


def _make_job(db_session, status=JobStatus.pending, retry_count=0, retry_after=None):
    job = Job(
        command="alert",
        args=json.dumps({"kwargs": {"host": "web01"}, "args": []}),
        thread_context={"channel_id": "C1", "thread_ts": "111.000", "user": "U1"},
        status=status,
        retry_count=retry_count,
        retry_after=retry_after,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


class TestClaimPendingJobs:

    def test_claim_returns_pending_jobs(self, db_session):
        """pending ジョブを取得して processing に変更する"""
        from src.domain.services.job_service import JobService

        _make_job(db_session)
        svc = JobService(
            db=db_session,
            max_concurrency=4,
            max_retry_count=3,
            retry_delay_seconds=60,
            slack_client=None,
        )
        jobs = svc.claim_pending_jobs()
        assert len(jobs) == 1
        assert jobs[0].status == JobStatus.processing

    def test_claim_skips_processing_jobs(self, db_session):
        """processing 状態のジョブは取得しない"""
        from src.domain.services.job_service import JobService

        _make_job(db_session, status=JobStatus.processing)
        svc = JobService(
            db=db_session,
            max_concurrency=4,
            max_retry_count=3,
            retry_delay_seconds=60,
            slack_client=None,
        )
        jobs = svc.claim_pending_jobs()
        assert jobs == []

    def test_claim_skips_future_retry_after(self, db_session):
        """retry_after が未来のジョブはスキップする"""
        from src.domain.services.job_service import JobService

        future = _utcnow() + timedelta(hours=1)
        _make_job(db_session, retry_after=future)
        svc = JobService(
            db=db_session,
            max_concurrency=4,
            max_retry_count=3,
            retry_delay_seconds=60,
            slack_client=None,
        )
        jobs = svc.claim_pending_jobs()
        assert jobs == []

    def test_claim_picks_past_retry_after(self, db_session):
        """retry_after が過去のジョブは取得する"""
        from src.domain.services.job_service import JobService

        past = _utcnow() - timedelta(hours=1)
        _make_job(db_session, retry_after=past)
        svc = JobService(
            db=db_session,
            max_concurrency=4,
            max_retry_count=3,
            retry_delay_seconds=60,
            slack_client=None,
        )
        jobs = svc.claim_pending_jobs()
        assert len(jobs) == 1

    def test_claim_respects_max_concurrency(self, db_session):
        """max_concurrency の上限数だけ取得する"""
        from src.domain.services.job_service import JobService

        for _ in range(5):
            _make_job(db_session)
        svc = JobService(
            db=db_session,
            max_concurrency=2,
            max_retry_count=3,
            retry_delay_seconds=60,
            slack_client=None,
        )
        jobs = svc.claim_pending_jobs()
        assert len(jobs) == 2


class TestMarkDone:

    def test_mark_done_sets_status(self, db_session):
        """mark_done でステータスが done になる"""
        from src.domain.services.job_service import JobService

        job = _make_job(db_session, status=JobStatus.processing)
        svc = JobService(
            db=db_session,
            max_concurrency=4,
            max_retry_count=3,
            retry_delay_seconds=60,
            slack_client=None,
        )
        svc.mark_done(job)
        db_session.refresh(job)
        assert job.status == JobStatus.done


class TestMarkFailed:

    def test_mark_failed_within_limit_sets_pending(self, db_session):
        """リトライ上限以内なら pending に戻して retry_count を増やす"""
        from src.domain.services.job_service import JobService

        job = _make_job(db_session, status=JobStatus.processing, retry_count=0)
        svc = JobService(
            db=db_session,
            max_concurrency=4,
            max_retry_count=3,
            retry_delay_seconds=60,
            slack_client=None,
        )
        svc.mark_failed(job, reason="timeout")
        db_session.refresh(job)
        assert job.status == JobStatus.pending
        assert job.retry_count == 1
        assert job.failure_reason == "timeout"
        assert job.retry_after is not None
        assert job.retry_after > _utcnow()

    def test_mark_failed_at_limit_sets_failed_and_notifies(self, db_session):
        """リトライ上限到達なら failed にして Slack 通知する"""
        from src.domain.services.job_service import JobService
        from unittest.mock import MagicMock

        slack = MagicMock()
        job = _make_job(db_session, status=JobStatus.processing, retry_count=3)
        svc = JobService(
            db=db_session,
            max_concurrency=4,
            max_retry_count=3,
            retry_delay_seconds=60,
            slack_client=slack,
        )
        svc.mark_failed(job, reason="command error")
        db_session.refresh(job)
        assert job.status == JobStatus.failed
        assert job.retry_count == 3  # 増えない
        slack.post_message.assert_called_once()

    def test_mark_failed_boundary_retry_count_2(self, db_session):
        """retry_count=2 (上限3) → まだリトライ可能"""
        from src.domain.services.job_service import JobService

        job = _make_job(db_session, status=JobStatus.processing, retry_count=2)
        svc = JobService(
            db=db_session,
            max_concurrency=4,
            max_retry_count=3,
            retry_delay_seconds=60,
            slack_client=None,
        )
        svc.mark_failed(job, reason="err")
        db_session.refresh(job)
        assert job.status == JobStatus.pending
        assert job.retry_count == 3
