from __future__ import annotations

import httpx


class SlackClient:
    """Slack 投稿プロキシへの薄いラッパー。"""

    def __init__(self, proxy_url: str) -> None:
        self._proxy_url = proxy_url

    def post_message(self, *, channel: str, thread_ts: str | None, text: str) -> None:
        """プロキシ経由でメッセージを Slack に投稿する。

        Args:
            channel: 投稿先チャンネル ID
            thread_ts: スレッドのタイムスタンプ（スレッド返信時に指定、不要なら None）
            text: 投稿するテキスト

        Raises:
            httpx.HTTPStatusError: HTTP 4xx / 5xx が返った場合
        """
        payload: dict[str, str] = {"channel": channel, "text": text}
        if thread_ts is not None:
            payload["thread_ts"] = thread_ts

        with httpx.Client() as client:
            response = client.post(self._proxy_url, json=payload)
            response.raise_for_status()
