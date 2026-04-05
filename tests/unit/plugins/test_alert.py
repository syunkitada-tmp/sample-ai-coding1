import json
import pytest
from unittest.mock import MagicMock


def _ctx():
    return {"channel_id": "C1", "thread_ts": "111.000", "user": "U1"}


class TestAlertPlugin:

    def test_success_with_host(self):
        """--host が指定されていれば実行結果を返す"""
        from src.plugins.alert import AlertPlugin

        plugin = AlertPlugin()
        result = plugin.execute(
            kwargs={"host": "web01"},
            args="",
            thread_context=_ctx(),
        )
        assert "web01" in result

    def test_success_with_host_and_positional_args(self):
        """--host と位置引数を含む場合も結果に反映される"""
        from src.plugins.alert import AlertPlugin

        plugin = AlertPlugin()
        result = plugin.execute(
            kwargs={"host": "web01"},
            args="app01",
            thread_context=_ctx(),
        )
        assert "web01" in result
        assert "app01" in result

    def test_host_missing_raises_no_retry_error(self):
        """--host がなければ NoRetryError を送出する"""
        from src.plugins.alert import AlertPlugin
        from src.domain.exceptions import NoRetryError

        plugin = AlertPlugin()
        with pytest.raises(NoRetryError, match="--host"):
            plugin.execute(
                kwargs={},
                args="app01",
                thread_context=_ctx(),
            )

    def test_command_name_and_description(self):
        """command_name と description が定義されている"""
        from src.plugins.alert import AlertPlugin

        plugin = AlertPlugin()
        assert plugin.command_name == "alert"
        assert plugin.description != ""


class TestExecutorNoRetryHandling:
    """executor が NoRetryError を受け取ったとき retry しない"""

    def test_no_retry_error_marks_failed_immediately(self):
        """NoRetryError は max_retry_count に達したとして mark_failed を呼ぶ"""
        from src.domain.exceptions import NoRetryError
        from src.worker.executor import WorkerExecutor
        import json

        job = MagicMock()
        job.id = 1
        job.command = "alert"
        job.args = json.dumps({"kwargs": {}, "args": "app01"})
        job.thread_context = _ctx()

        plugin = MagicMock()
        plugin.execute.side_effect = NoRetryError("--host is required")

        plugin_loader = MagicMock()
        plugin_loader.get.return_value = plugin

        job_svc = MagicMock()
        slack = MagicMock()

        executor = WorkerExecutor(
            job_service=job_svc,
            plugin_loader=plugin_loader,
            slack_client=slack,
            max_workers=1,
        )
        executor._execute_job(job)

        job_svc.mark_failed_no_retry.assert_called_once_with(
            job, reason="--host is required"
        )
        job_svc.mark_failed.assert_not_called()
