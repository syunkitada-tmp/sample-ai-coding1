import json
import pytest
from concurrent.futures import Future
from unittest.mock import MagicMock, patch

from src.domain.models.job import Job, JobStatus


# ---------------------------------------------------------------------------
# sync pool fixture
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def sync_pool(mocker):
    """テスト用: ThreadPoolExecutor.submit を submit の呑出し元スレッドで同期実行する。

    これにより run_once() 内で投入した Future が即座に done になり、
    非ブロッキング設計でもテストが deterministic になる。
    """
    original_init = __import__(
        "concurrent.futures", fromlist=["ThreadPoolExecutor"]
    ).ThreadPoolExecutor.__init__

    class _SyncPool:
        def __init__(self, max_workers=None):
            pass

        def submit(self, fn, *args, **kwargs):
            f = Future()
            f.set_running_or_notify_cancel()
            try:
                f.set_result(fn(*args, **kwargs))
            except Exception as exc:
                f.set_exception(exc)
            return f

        def shutdown(self, wait=True):
            pass

    mocker.patch("src.worker.executor.ThreadPoolExecutor", _SyncPool)


def _make_mock_job(job_id=1, command="alert", retry_count=0):
    job = MagicMock(spec=Job)
    job.id = job_id
    job.command = command
    job.args = json.dumps({"kwargs": {"host": "web01"}, "args": []})
    job.thread_context = {"channel_id": "C1", "thread_ts": "111.000", "user": "U1"}
    job.status = JobStatus.processing
    job.retry_count = retry_count
    return job


def _make_job_service(claimed_jobs=None):
    svc = MagicMock()
    # 1回目の呼び出しだけジョブを返し、以降は空を返す（2回目の run_once() で再取得しないように）
    _jobs = claimed_jobs or []
    _called = []

    def _claim(limit=None):
        if not _called:
            _called.append(True)
            return _jobs
        return []

    svc.claim_pending_jobs.side_effect = _claim
    svc.mark_done = MagicMock()
    svc.mark_failed = MagicMock()
    return svc


def _make_plugin_loader(succeed=True):
    loader = MagicMock()
    plugin = MagicMock()
    if succeed:
        plugin.execute.return_value = "ok"
    else:
        plugin.execute.side_effect = RuntimeError("command error")
    loader.get.return_value = plugin
    return loader


class TestWorkerExecutor:

    def test_run_once_executes_pending_job(self):
        """pending ジョブを取得してプラグインを実行し done にする"""
        from src.worker.executor import WorkerExecutor

        job = _make_mock_job()
        job_svc = _make_job_service(claimed_jobs=[job])
        plugin_loader = _make_plugin_loader(succeed=True)
        slack = MagicMock()

        executor = WorkerExecutor(
            job_service=job_svc,
            plugin_loader=plugin_loader,
            slack_client=slack,
            max_workers=4,
        )
        executor.run_once()  # 投入（sync_pool なので即座実行完了）
        executor.run_once()  # 完了済み Future を回収

        plugin_loader.get.assert_called_once_with("alert")
        plugin_loader.get.return_value.execute.assert_called_once()
        job_svc.mark_done.assert_called_once_with(job)
        job_svc.mark_failed.assert_not_called()

    def test_run_once_marks_failed_on_plugin_error(self):
        """プラグイン実行失敗時に mark_failed を呼ぶ"""
        from src.worker.executor import WorkerExecutor

        job = _make_mock_job()
        job_svc = _make_job_service(claimed_jobs=[job])
        plugin_loader = _make_plugin_loader(succeed=False)
        slack = MagicMock()

        executor = WorkerExecutor(
            job_service=job_svc,
            plugin_loader=plugin_loader,
            slack_client=slack,
            max_workers=4,
        )
        executor.run_once()
        executor.run_once()  # 完了済み Future を回収

        job_svc.mark_failed.assert_called_once_with(job, reason="command error")
        job_svc.mark_done.assert_not_called()

    def test_run_once_posts_result_to_slack(self):
        """実行結果を Slack スレッドに投稿する"""
        from src.worker.executor import WorkerExecutor

        job = _make_mock_job()
        job_svc = _make_job_service(claimed_jobs=[job])
        plugin_loader = _make_plugin_loader(succeed=True)
        plugin_loader.get.return_value.execute.return_value = "done!"
        slack = MagicMock()

        executor = WorkerExecutor(
            job_service=job_svc,
            plugin_loader=plugin_loader,
            slack_client=slack,
            max_workers=4,
        )
        executor.run_once()
        executor.run_once()

        slack.post_message.assert_called_once()
        _, kwargs = slack.post_message.call_args
        assert kwargs["text"] == "done!"
        assert kwargs["channel"] == "C1"
        assert kwargs["thread_ts"] == "111.000"

    def test_run_once_no_jobs_does_nothing(self):
        """ジョブがなければ何もしない"""
        from src.worker.executor import WorkerExecutor

        job_svc = _make_job_service(claimed_jobs=[])
        executor = WorkerExecutor(
            job_service=job_svc,
            plugin_loader=MagicMock(),
            slack_client=MagicMock(),
            max_workers=4,
        )
        executor.run_once()
        job_svc.mark_done.assert_not_called()
        job_svc.mark_failed.assert_not_called()

    def test_run_once_executes_multiple_jobs_concurrently(self):
        """複数ジョブが全て処理される（並行実行）"""
        from src.worker.executor import WorkerExecutor

        jobs = [_make_mock_job(job_id=i) for i in range(3)]
        job_svc = _make_job_service(claimed_jobs=jobs)
        plugin_loader = _make_plugin_loader(succeed=True)
        slack = MagicMock()

        executor = WorkerExecutor(
            job_service=job_svc,
            plugin_loader=plugin_loader,
            slack_client=slack,
            max_workers=3,
        )
        executor.run_once()
        executor.run_once()  # 完了済み Future を回収

        assert job_svc.mark_done.call_count == 3

    def test_run_once_fills_free_slots_on_subsequent_call(self):
        """スロットが空くと次の run_once() で新規ジョブが投入される"""
        from src.worker.executor import WorkerExecutor

        jobs_batch1 = [_make_mock_job(job_id=i) for i in range(2)]
        jobs_batch2 = [_make_mock_job(job_id=10)]

        job_svc = MagicMock()
        # 1回目: 2 ジョブ, 2回目(Future 回収後): 1 ジョブ, 3回目: 0 ジョブ
        job_svc.claim_pending_jobs.side_effect = [jobs_batch1, jobs_batch2, []]
        job_svc.mark_done = MagicMock()
        job_svc.mark_failed = MagicMock()

        executor = WorkerExecutor(
            job_service=job_svc,
            plugin_loader=_make_plugin_loader(succeed=True),
            slack_client=MagicMock(),
            max_workers=2,
        )
        executor.run_once()  # batch1 を投入（sync_pool で即座実行完了）
        executor.run_once()  # Future 回収 + batch2 を投入
        executor.run_once()  # Future 回収 + 新規なし

        assert job_svc.mark_done.call_count == 3
        # 2回目の claim には limit=2（free_slots）が渡る
        assert job_svc.claim_pending_jobs.call_count == 3

    def test_execute_job_restores_trace_id_to_context(self):
        """_execute_job 実行後、get_trace_id() がジョブの trace_id と一致する"""
        from src.lib.logging import get_trace_id, set_trace_id
        from src.worker.executor import WorkerExecutor

        job = _make_mock_job()
        job.trace_id = "job-trace-abc"
        job_svc = _make_job_service(claimed_jobs=[job])
        plugin_loader = _make_plugin_loader(succeed=True)
        slack = MagicMock()

        captured = []

        original_execute = plugin_loader.get.return_value.execute

        def capture_trace_id(*args, **kwargs):
            captured.append(get_trace_id())
            return "ok"

        plugin_loader.get.return_value.execute = capture_trace_id

        executor = WorkerExecutor(
            job_service=job_svc,
            plugin_loader=plugin_loader,
            slack_client=slack,
            max_workers=4,
        )
        set_trace_id(None)  # 事前にリセット
        executor.run_once()
        executor.run_once()

        assert captured == ["job-trace-abc"]
        set_trace_id(None)  # クリーンアップ
