import json
import pytest
from unittest.mock import MagicMock, patch

from src.domain.models.message import Message
from src.domain.models.job import Job, JobStatus


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _make_slack_client():
    mock = MagicMock()
    mock.post_message = MagicMock()
    return mock


def _make_plugin_loader(registered_commands: list[str]):
    mock = MagicMock()
    mock.get = lambda cmd: object() if cmd in registered_commands else None
    return mock


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------


class TestMessageService:

    def test_plain_message_is_saved_no_job(self, db_session):
        """コマンドなしメッセージはジョブを作らずに保存される"""
        from src.domain.services.message_service import MessageService

        svc = MessageService(
            db=db_session,
            slack_client=_make_slack_client(),
            plugin_loader=_make_plugin_loader(["alert"]),
        )
        svc.handle(
            channel_id="C123",
            thread_ts="111.000",
            user="U1",
            text="Good morning",
            timestamp="111.000",
        )
        db_session.flush()
        assert db_session.query(Message).count() == 1
        assert db_session.query(Job).count() == 0

    def test_valid_command_creates_job(self, db_session):
        """既知コマンドのメッセージはジョブを pending で作成する"""
        from src.domain.services.message_service import MessageService

        svc = MessageService(
            db=db_session,
            slack_client=_make_slack_client(),
            plugin_loader=_make_plugin_loader(["alert"]),
        )
        svc.handle(
            channel_id="C123",
            thread_ts="111.000",
            user="U1",
            text="!alert --host web01",
            timestamp="111.000",
        )
        db_session.flush()
        assert db_session.query(Message).count() == 1
        jobs = db_session.query(Job).all()
        assert len(jobs) == 1
        job = jobs[0]
        assert job.command == "alert"
        assert job.status == JobStatus.pending
        parsed = json.loads(job.args)
        assert parsed["kwargs"] == {"host": "web01"}
        assert parsed["args"] == []

    def test_job_contains_thread_context(self, db_session):
        """ジョブレコードにスレッドコンテキストが格納される"""
        from src.domain.services.message_service import MessageService

        svc = MessageService(
            db=db_session,
            slack_client=_make_slack_client(),
            plugin_loader=_make_plugin_loader(["alert"]),
        )
        svc.handle(
            channel_id="C123",
            thread_ts="111.000",
            user="U1",
            text="!alert --host web01",
            timestamp="111.000",
        )
        db_session.flush()
        job = db_session.query(Job).one()
        ctx = job.thread_context
        assert ctx["channel_id"] == "C123"
        assert ctx["thread_ts"] == "111.000"
        assert ctx["user"] == "U1"

    def test_multiple_commands_saves_message_and_notifies(self, db_session):
        """複数コマンドはメッセージ保存 + Slack エラー通知のみ（ジョブなし）"""
        from src.domain.services.message_service import MessageService

        slack = _make_slack_client()
        svc = MessageService(
            db=db_session,
            slack_client=slack,
            plugin_loader=_make_plugin_loader(["alert", "help"]),
        )
        svc.handle(
            channel_id="C123",
            thread_ts="111.000",
            user="U1",
            text="!alert --host web01\n!help",
            timestamp="111.000",
        )
        db_session.flush()
        assert db_session.query(Message).count() == 1
        assert db_session.query(Job).count() == 0
        slack.post_message.assert_called_once()

    def test_unknown_command_saves_message_and_notifies(self, db_session):
        """未知コマンドはメッセージ保存 + Slack エラー通知（ジョブなし）"""
        from src.domain.services.message_service import MessageService

        slack = _make_slack_client()
        svc = MessageService(
            db=db_session,
            slack_client=slack,
            plugin_loader=_make_plugin_loader([]),  # 何も登録されていない
        )
        svc.handle(
            channel_id="C123",
            thread_ts="111.000",
            user="U1",
            text="!unknown --foo bar",
            timestamp="111.000",
        )
        db_session.flush()
        assert db_session.query(Message).count() == 1
        assert db_session.query(Job).count() == 0
        slack.post_message.assert_called_once()

    def test_atomicity_on_db_error(self, db_session, mocker):
        """DB 書き込み失敗時にメッセージもジョブも残らない"""
        from src.domain.services.message_service import MessageService

        svc = MessageService(
            db=db_session,
            slack_client=_make_slack_client(),
            plugin_loader=_make_plugin_loader(["alert"]),
        )
        mocker.patch.object(db_session, "commit", side_effect=Exception("DB error"))
        with pytest.raises(Exception, match="DB error"):
            svc.handle(
                channel_id="C123",
                thread_ts="111.000",
                user="U1",
                text="!alert --host web01",
                timestamp="111.000",
            )
        assert db_session.query(Message).count() == 0
        assert db_session.query(Job).count() == 0
