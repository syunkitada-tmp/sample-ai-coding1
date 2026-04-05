"""Integration tests: API → DB 実際書き込みの E2E 検証。

MySQL は不要。SQLite インメモリ DB + 実際の MessageService を使用する。
"""

import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock

from src.domain.models.base import Base
from src.domain.models.message import Message
from src.domain.models.job import Job, JobStatus
from src.domain.interfaces.plugin import CommandRegistry


# ---------------------------------------------------------------------------
# フィクスチャ
# ---------------------------------------------------------------------------


@pytest.fixture
def integration_client():
    """SQLite インメモリ DB + モック SlackClient + 実際の MessageService を使う TestClient"""
    from sqlalchemy.pool import StaticPool
    from src.api.main import create_app
    from src.api import dependencies
    from src.infrastructure.plugin_loader import PluginLoader
    from src.domain.services.message_service import MessageService

    # StaticPool: 全接続で同一インメモリ DB を共有する
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    # プラグインローダー
    loader = PluginLoader()
    # 統合テスト用にシェルコマンドを手動登録
    loader.register_command(CommandRegistry("alert", "/bin/echo", "アラート送信"))
    loader.register_command(CommandRegistry("help", "/bin/echo", "ヘルプ"))

    # SlackClient はモック
    mock_slack = MagicMock()
    mock_slack.post_message = MagicMock()

    app = create_app()

    def override_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def override_message_service():
        db = SessionLocal()
        return MessageService(db=db, slack_client=mock_slack, plugin_loader=loader)

    app.dependency_overrides[dependencies.get_db] = override_db
    app.dependency_overrides[dependencies.get_message_service] = (
        override_message_service
    )

    client = TestClient(app)
    yield client, SessionLocal, mock_slack

    Base.metadata.drop_all(engine)


# ---------------------------------------------------------------------------
# テスト
# ---------------------------------------------------------------------------


class TestReceiveMessageIntegration:

    def test_plain_message_saved_no_job(self, integration_client):
        """コマンドなしメッセージ: messages のみ保存、jobs なし"""
        client, Session, slack = integration_client
        resp = client.post(
            "/messages",
            json={
                "channel_id": "C123",
                "thread_ts": "111.000",
                "user": "U1",
                "text": "Good morning",
                "timestamp": "111.000",
            },
        )
        assert resp.status_code == 200

        db = Session()
        assert db.query(Message).count() == 1
        assert db.query(Job).count() == 0
        db.close()

    def test_valid_command_creates_pending_job(self, integration_client):
        """既知コマンド: message + job(pending) が作成される"""
        client, Session, slack = integration_client
        resp = client.post(
            "/messages",
            json={
                "channel_id": "C123",
                "thread_ts": "111.000",
                "user": "U1",
                "text": "!alert --host web01",
                "timestamp": "111.000",
            },
        )
        assert resp.status_code == 200

        db = Session()
        assert db.query(Message).count() == 1
        jobs = db.query(Job).all()
        assert len(jobs) == 1
        assert jobs[0].command == "alert"
        assert jobs[0].status == JobStatus.pending
        parsed = json.loads(jobs[0].args)
        assert parsed["kwargs"] == {"host": "web01"}
        db.close()

    def test_job_contains_thread_context(self, integration_client):
        """ジョブレコードにスレッドコンテキストが格納される"""
        client, Session, slack = integration_client
        resp = client.post(
            "/messages",
            json={
                "channel_id": "C123",
                "thread_ts": "111.000",
                "user": "U1",
                "text": "!alert --host web01",
                "timestamp": "111.000",
            },
        )
        assert resp.status_code == 200
        db = Session()
        job = db.query(Job).one()
        assert job.thread_context["channel_id"] == "C123"
        assert job.thread_context["thread_ts"] == "111.000"
        db.close()

    def test_multiple_commands_notifies_slack(self, integration_client):
        """複数コマンド: messages 保存 + Slack 通知、jobs なし"""
        client, Session, slack = integration_client
        resp = client.post(
            "/messages",
            json={
                "channel_id": "C123",
                "thread_ts": "111.000",
                "user": "U1",
                "text": "!alert --host web01\n!help",
                "timestamp": "111.000",
            },
        )
        assert resp.status_code == 200
        db = Session()
        assert db.query(Message).count() == 1
        assert db.query(Job).count() == 0
        db.close()
        slack.post_message.assert_called_once()

    def test_unknown_command_notifies_slack(self, integration_client):
        """未知コマンド: messages 保存 + Slack 通知、jobs なし"""
        client, Session, slack = integration_client
        resp = client.post(
            "/messages",
            json={
                "channel_id": "C123",
                "thread_ts": "111.000",
                "user": "U1",
                "text": "!unknown --foo bar",
                "timestamp": "111.000",
            },
        )
        assert resp.status_code == 200
        db = Session()
        assert db.query(Message).count() == 1
        assert db.query(Job).count() == 0
        db.close()
        slack.post_message.assert_called_once()

    def test_missing_required_field_returns_422(self, integration_client):
        """必須フィールド欠如: 422 が返る"""
        client, _, _ = integration_client
        resp = client.post(
            "/messages",
            json={
                "channel_id": "C123",
                "user": "U1",
                # text が欠如
                "timestamp": "111.000",
            },
        )
        assert resp.status_code == 422
