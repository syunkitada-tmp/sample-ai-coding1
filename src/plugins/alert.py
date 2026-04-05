from __future__ import annotations

from src.domain.exceptions import NoRetryError
from src.domain.interfaces.plugin import BasePlugin


class AlertPlugin(BasePlugin):
    """ホスト指定アラートのダミー実装プラグイン。

    --host が必須。不足の場合はリトライなし失敗 (NoRetryError) を送出する。
    成功時は受けたオプション・引数とスレッドコンテキストをエコーバックする。
    """

    command_name = "alert"
    description = "アラートを送信します (--host <host> が必須)"

    def execute(
        self,
        kwargs: dict[str, str | bool],
        args: str,
        thread_context: dict,
    ) -> str:
        host = kwargs.get("host")
        if not host:
            raise NoRetryError("--host is required")

        parts = [f"alert executed: host={host}"]
        if args:
            parts.append(f"args={args}")
        parts.append(
            f"channel={thread_context.get('channel_id')} "
            f"thread={thread_context.get('thread_ts')}"
        )
        return "\n".join(parts)
