import json
import pytest
from concurrent.futures import Future
from unittest.mock import MagicMock, patch

from src.domain.models.job import Job, JobStatus
from src.domain.interfaces.plugin import CommandRegistry


# ---------------------------------------------------------------------------
# sync pool fixture
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def sync_pool(mocker):
    """テスト用: ThreadPoolExecutor.submit を submit の呑出し元スレッドで同期実行する。

    これにより run_once() 内で投入した Future が即座に done になり、
    非ブロッキング設計でもテストが deterministic になる。
    """
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
    job.args = json.dumps({"kwargs": {"host": "web01"}, "args": ""})
    job.thread_context = {"channel_id": "C1", "thread_ts": "111.000", "user": "U1"}
    job.status = JobStatus.processing
    job.retry_count = retry_count
    job.trace_id = f"trace-{job_id}"
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
    svc.mark_failed_no_retry = MagicMock()
    return svc


def _make_plugin_loader(command="alert"):
    loader = MagicMock()
    registry = CommandRegistry(command, f"/path/to/{command}", f"{command} desc")
    loader.get.return_value = registry
    return loader


class TestWorkerExecutor:

    @patch("src.worker.executor.subprocess.run")
    def test_run_once_executes_pending_job(self, mock_run):
        """pending ジョブを取得してシェルコマンドを実行し done にする"""
        from src.worker.executor import WorkerExecutor

        mock_run.return_value = MagicMock(returncode=0, stdout='{"result": "ok"}')
        job = _make_mock_job()
        job_svc = _make_job_service(claimed_jobs=[job])
        plugin_loader = _make_plugin_loader()
        slack = MagicMock()

        executor = WorkerExecutor(
            job_service=job_svc,
            plugin_loader=plugin_loader,
            slack_client=slack,
            max_workers=4,
            command_timeout=30,
        )
        executor.run_once()  # 投入（sync_pool なので即座実行完了）
        executor.run_once()  # 完了済み Future を回収

        plugin_loader.get.assert_called_once_with("alert")
        mock_run.assert_called_once()
        job_svc.mark_done.assert_called_once_with(job)
        job_svc.mark_failed.assert_not_called()

    @patch("src.worker.executor.subprocess.run")
    def test_run_once_marks_failed_on_command_error(self, mock_run):
        """コマンド実行失敗時に mark_failed を呼ぶ"""
        from src.worker.executor import WorkerExecutor

        mock_run.return_value = MagicMock(returncode=1, stdout='', stderr="error")
        job = _make_mock_job()
        job_svc = _make_job_service(claimed_jobs=[job])
        plugin_loader = _make_plugin_loader()
        slack = MagicMock()

        executor = WorkerExecutor(
            job_service=job_svc,
            plugin_loader=plugin_loader,
            slack_client=slack,
            max_workers=4,
            command_timeout=30,
        )
        executor.run_once()
        executor.run_once()

        job_svc.mark_failed.assert_called_once()
        job_svc.mark_done.assert_not_called()

    @patch("src.worker.executor.subprocess.run")
    def test_run_once_posts_result_to_slack(self, mock_run):
        """実行結果を Slack スレッドに投稿する"""
        from src.worker.executor import WorkerExecutor

        mock_run.return_value = MagicMock(returncode=0, stdout='{"result": "done!"}')
        job = _make_mock_job()
        job_svc = _make_job_service(claimed_jobs=[job])
        plugin_loader = _make_plugin_loader()
        slack = MagicMock()

        executor = WorkerExecutor(
            job_service=job_svc,
            plugin_loader=plugin_loader,
            slack_client=slack,
            max_workers=4,
            command_timeout=30,
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
            command_timeout=30,
        )
        executor.run_once()
        job_svc.mark_done.assert_not_called()
        job_svc.mark_failed.assert_not_called()

    @patch("src.worker.executor.subprocess.run")
    def test_run_once_executes_multiple_jobs_concurrently(self, mock_run):
        """複数ジョブが全て処理される（並行実行）"""
        from src.worker.executor import WorkerExecutor

        mock_run.return_value = MagicMock(returncode=0, stdout='ok')
        jobs = [_make_mock_job(job_id=i) for i in range(3)]
        job_svc = _make_job_service(claimed_jobs=jobs)
        plugin_loader = _make_plugin_loader()
        slack = MagicMock()

        executor = WorkerExecutor(
            job_service=job_svc,
            plugin_loader=plugin_loader,
            slack_client=slack,
            max_workers=3,
            command_timeout=30,
        )
        executor.run_once()
        executor.run_once()

        assert job_svc.mark_done.call_count == 3

    @patch("src.worker.executor.subprocess.run")
    def test_run_once_fills_free_slots_on_subsequent_call(self, mock_run):
        """スロットが空くと次の run_once() で新規ジョブが投入される"""
        from src.worker.executor import WorkerExecutor

        mock_run.return_value = MagicMock(returncode=0, stdout='ok')
        jobs_batch1 = [_make_mock_job(job_id=i) for i in range(2)]
        jobs_batch2 = [_make_mock_job(job_id=10)]

        job_svc = MagicMock()
        job_svc.claim_pending_jobs.side_effect = [jobs_batch1, jobs_batch2, []]
        job_svc.mark_done = MagicMock()
        job_svc.mark_failed = MagicMock()

        executor = WorkerExecutor(
            job_service=job_svc,
            plugin_loader=_make_plugin_loader(),
            slack_client=MagicMock(),
            max_workers=2,
            command_timeout=30,
        )
        executor.run_once()  # batch1 を投入
        executor.run_once()  # Future 回収 + batch2 を投入
        executor.run_once()  # Future 回収 + 新規なし

        assert job_svc.mark_done.call_count == 3
        assert job_svc.claim_pending_jobs.call_count == 3

    @patch("src.worker.executor.subprocess.run")
    def test_execute_job_restores_trace_id_to_context(self, mock_run):
        """_execute_job 実行中、get_trace_id() がジョブの trace_id と一致する"""
        from src.lib.logging import get_trace_id, set_trace_id
        from src.worker.executor import WorkerExecutor

        mock_run.side_effect = lambda *args, **kwargs: MagicMock(returncode=0, stdout=get_trace_id())

        job = _make_mock_job()
        job.trace_id = "job-trace-abc"
        job_svc = _make_job_service(claimed_jobs=[job])
        plugin_loader = _make_plugin_loader()
        slack = MagicMock()

        executor = WorkerExecutor(
            job_service=job_svc,
            plugin_loader=plugin_loader,
            slack_client=slack,
            max_workers=4,
            command_timeout=30,
        )
        set_trace_id(None)
        executor.run_once()
        executor.run_once()

        slack.post_message.assert_called_once()
        assert slack.post_message.call_args[1]["text"] == "job-trace-abc"
        set_trace_id(None)

    @patch("src.worker.executor.subprocess.run")
    def test_execute_shell_success_json(self, mock_run):
        from src.worker.executor import WorkerExecutor

        mock_run.return_value = MagicMock(returncode=0, stdout='{"result": "alert ok"}')
        job = _make_mock_job()
        job_svc = _make_job_service(claimed_jobs=[job])
        plugin_loader = _make_plugin_loader()
        slack = MagicMock()

        executor = WorkerExecutor(
            job_service=job_svc, plugin_loader=plugin_loader, slack_client=slack,
            max_workers=1, command_timeout=30,
        )
        executor.run_once()
        executor.run_once()

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "/path/to/alert"
        assert "--host" in args
        assert "web01" in args

        slack.post_message.assert_called_once()
        assert slack.post_message.call_args[1]["text"] == "alert ok"
        job_svc.mark_done.assert_called_once_with(job)

    @patch("src.worker.executor.subprocess.run")
    def test_execute_shell_success_plaintext(self, mock_run):
        from src.worker.executor import WorkerExecutor

        mock_run.return_value = MagicMock(returncode=0, stdout='plain text output')
        job = _make_mock_job()
        job_svc = _make_job_service(claimed_jobs=[job])
        plugin_loader = _make_plugin_loader()
        slack = MagicMock()

        executor = WorkerExecutor(
            job_service=job_svc, plugin_loader=plugin_loader, slack_client=slack,
            max_workers=1, command_timeout=30,
        )
        executor.run_once()
        executor.run_once()

        slack.post_message.assert_called_once()
        assert slack.post_message.call_args[1]["text"] == "plain text output"
        job_svc.mark_done.assert_called_once_with(job)

    @patch("src.worker.executor.subprocess.run")
    def test_execute_shell_timeout(self, mock_run):
        from src.worker.executor import WorkerExecutor
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=30)
        job = _make_mock_job()
        job_svc = _make_job_service(claimed_jobs=[job])
        plugin_loader = _make_plugin_loader()
        slack = MagicMock()

        executor = WorkerExecutor(
            job_service=job_svc, plugin_loader=plugin_loader, slack_client=slack,
            max_workers=1, command_timeout=30,
        )
        executor.run_once()
        executor.run_once()

        job_svc.mark_failed.assert_called_once()
        assert "Command timed out" in job_svc.mark_failed.call_args[1]["reason"]

    @patch("src.worker.executor.subprocess.run")
    def test_execute_shell_not_found(self, mock_run):
        from src.worker.executor import WorkerExecutor

        mock_run.side_effect = FileNotFoundError()
        job = _make_mock_job()
        job_svc = _make_job_service(claimed_jobs=[job])
        plugin_loader = _make_plugin_loader()
        slack = MagicMock()

        executor = WorkerExecutor(
            job_service=job_svc, plugin_loader=plugin_loader, slack_client=slack,
            max_workers=1, command_timeout=30,
        )
        executor.run_once()
        executor.run_once()

        job_svc.mark_failed_no_retry.assert_called_once()
        assert "Command not found" in job_svc.mark_failed_no_retry.call_args[1]["reason"]

    @patch("src.worker.executor.subprocess.run")
    def test_execute_shell_error_json(self, mock_run):
        from src.worker.executor import WorkerExecutor

        mock_run.return_value = MagicMock(returncode=1, stdout='{"error": "user error"}', stderr="")
        job = _make_mock_job()
        job_svc = _make_job_service(claimed_jobs=[job])
        plugin_loader = _make_plugin_loader()
        slack = MagicMock()

        executor = WorkerExecutor(
            job_service=job_svc, plugin_loader=plugin_loader, slack_client=slack,
            max_workers=1, command_timeout=30,
        )
        executor.run_once()
        executor.run_once()

        job_svc.mark_failed_no_retry.assert_called_once()
        assert "user error" in job_svc.mark_failed_no_retry.call_args[1]["reason"]

    @patch("src.worker.executor.subprocess.run")
    def test_execute_shell_error_nonzero_exit(self, mock_run):
        from src.worker.executor import WorkerExecutor

        mock_run.return_value = MagicMock(returncode=1, stdout='some output', stderr="some error")
        job = _make_mock_job()
        job_svc = _make_job_service(claimed_jobs=[job])
        plugin_loader = _make_plugin_loader()
        slack = MagicMock()

        executor = WorkerExecutor(
            job_service=job_svc, plugin_loader=plugin_loader, slack_client=slack,
            max_workers=1, command_timeout=30,
        )
        executor.run_once()
        executor.run_once()

        job_svc.mark_failed.assert_called_once()
        assert "some error" in job_svc.mark_failed.call_args[1]["reason"]
