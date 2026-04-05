from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, Future
from typing import TYPE_CHECKING

from src.lib.logging import set_trace_id
from src.domain.exceptions import NoRetryError
from src.domain.models.job import Job

if TYPE_CHECKING:
    from src.domain.services.job_service import JobService
    from src.infrastructure.plugin_loader import PluginLoader
    from src.infrastructure.slack_client import SlackClient

logger = logging.getLogger(__name__)


class WorkerExecutor:
    """ThreadPoolExecutor でジョブを継続的に並行実行するワーカー。

    プールはインスタンスのライフタイムと同期し、run_once() は非ブロッキング。
    呼び出しごとに完了済み Future を回収して空きスロットに新規ジョブを投入する。
    これにより、1 ジョブが完了すると即座に次のジョブが開始できる。
    """

    def __init__(
        self,
        *,
        job_service: JobService,
        plugin_loader: PluginLoader,
        slack_client: SlackClient,
        max_workers: int,
    ) -> None:
        self._job_svc = job_service
        self._plugins = plugin_loader
        self._slack = slack_client
        self._max_workers = max_workers
        self._pool = ThreadPoolExecutor(max_workers=max_workers)
        self._active: set[Future] = set()

    def run_once(self) -> None:
        """完了済み Future を回収し、空きスロット分だけ新規ジョブを投入する（非ブロッキング）。

        - 投入されたジョブはバックグラウンドスレッドで並行実行を継続する。
        - 次の run_once() 呼び出し時に完了分を回収してスロットを再充填する。
        """
        # --- 完了済み Future を回収 ---
        done = {f for f in self._active if f.done()}
        for f in done:
            self._active.discard(f)
            try:
                f.result()
            except Exception as exc:  # _execute_job 内で通常は吸収済み
                logger.error("Unhandled error in job future: %s", exc, exc_info=True)

        # --- 空きスロット分だけ新規ジョブを取得して投入 ---
        free_slots = self._max_workers - len(self._active)
        if free_slots <= 0:
            return

        jobs = self._job_svc.claim_pending_jobs(limit=free_slots)
        for job in jobs:
            future = self._pool.submit(self._execute_job, job)
            self._active.add(future)

    def shutdown(self) -> None:
        """未完了ジョブの終了を待ってプールを停止する。"""
        self._pool.shutdown(wait=True)

    def _execute_job(self, job: Job) -> None:
        """単一ジョブの実行・結果通知・ステータス更新を行う。

        プラグインが見つからない場合も失敗として処理する。
        """
        set_trace_id(job.trace_id or "-")
        try:
            plugin = self._plugins.get(job.command)
            if plugin is None:
                self._job_svc.mark_failed(
                    job, reason=f"plugin '{job.command}' not found"
                )
                return

            parsed = json.loads(job.args) if job.args else {"kwargs": {}, "args": ""}
            kwargs = parsed.get("kwargs", {})
            args = parsed.get("args", "")
            ctx = job.thread_context

            try:
                result = plugin.execute(kwargs=kwargs, args=args, thread_context=ctx)
                self._slack.post_message(
                    channel=ctx.get("channel_id", ""),
                    thread_ts=ctx.get("thread_ts"),
                    text=result,
                )
                self._job_svc.mark_done(job)
            except NoRetryError as exc:
                self._job_svc.mark_failed_no_retry(job, reason=str(exc))
            except Exception as exc:
                self._job_svc.mark_failed(job, reason=str(exc))
        finally:
            set_trace_id(None)
