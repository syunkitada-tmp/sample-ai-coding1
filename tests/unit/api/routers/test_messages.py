import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def app(db_session):
    """テスト用 FastAPI アプリ。MessageService をモックに差し替える。"""
    from src.api.main import create_app
    from src.api import dependencies

    mock_svc = MagicMock()
    mock_svc.handle = MagicMock()

    app = create_app()
    app.dependency_overrides[dependencies.get_message_service] = lambda: mock_svc
    return app, mock_svc


@pytest.fixture
def client(app):
    application, _ = app
    return TestClient(application), app[1]


# ---------------------------------------------------------------------------
# POST /messages — 成功系
# ---------------------------------------------------------------------------


def test_receive_message_returns_200(client):
    tc, svc = client
    resp = tc.post(
        "/messages",
        json={
            "channel_id": "C123",
            "thread_ts": "1234567890.000100",
            "user": "U456",
            "text": "Hello",
            "timestamp": "1234567890.000100",
        },
    )
    assert resp.status_code == 200
    svc.handle.assert_called_once()


def test_receive_message_thread_ts_optional(client):
    tc, svc = client
    resp = tc.post(
        "/messages",
        json={
            "channel_id": "C123",
            "user": "U456",
            "text": "Hello",
            "timestamp": "1234567890.000100",
        },
    )
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# POST /messages — バリデーション失敗系
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("missing_field", ["channel_id", "user", "text", "timestamp"])
def test_missing_required_field_returns_400(client, missing_field):
    tc, _ = client
    body = {
        "channel_id": "C123",
        "user": "U456",
        "text": "Hello",
        "timestamp": "1234567890.000100",
    }
    del body[missing_field]
    resp = tc.post("/messages", json=body)
    assert resp.status_code == 422  # FastAPI は missing field に 422 を返す


def test_empty_body_returns_422(client):
    tc, _ = client
    resp = tc.post("/messages", json={})
    assert resp.status_code == 422


def test_no_body_returns_422(client):
    tc, _ = client
    resp = tc.post("/messages")
    assert resp.status_code == 422
