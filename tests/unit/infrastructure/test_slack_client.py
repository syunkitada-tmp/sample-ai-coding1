import pytest
import httpx


@pytest.fixture
def client():
    from src.infrastructure.slack_client import SlackClient

    return SlackClient(proxy_url="https://slack-proxy.example.com/post")


def test_post_message_sends_correct_payload(client, respx_mock):
    """正しいペイロードで POST が送信されること"""
    route = respx_mock.post("https://slack-proxy.example.com/post").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    client.post_message(channel="C123", thread_ts="1234567890.000100", text="hello")
    assert route.called
    payload = route.calls[0].request
    import json

    body = json.loads(payload.content)
    assert body["channel"] == "C123"
    assert body["thread_ts"] == "1234567890.000100"
    assert body["text"] == "hello"


def test_post_message_without_thread_ts(client, respx_mock):
    """thread_ts なしでも POST できること"""
    route = respx_mock.post("https://slack-proxy.example.com/post").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    client.post_message(channel="C123", thread_ts=None, text="hello")
    assert route.called
    import json

    body = json.loads(route.calls[0].request.content)
    assert "thread_ts" not in body


def test_post_message_raises_on_http_error(client, respx_mock):
    """5xx エラー時に例外が送出されること"""
    respx_mock.post("https://slack-proxy.example.com/post").mock(
        return_value=httpx.Response(500)
    )
    with pytest.raises(httpx.HTTPStatusError):
        client.post_message(channel="C123", thread_ts=None, text="error")
