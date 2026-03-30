from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from src.lib.logging import get_trace_id
from src.domain.exceptions import CommandSyntaxError, MultipleCommandsError
from src.domain.models.job import Job, JobStatus
from src.domain.models.message import Message
from src.domain.services.command_parser import parse_command

if TYPE_CHECKING:
    from src.infrastructure.plugin_loader import PluginLoader
    from src.infrastructure.slack_client import SlackClient


class MessageService:
    """受信メッセージの永続化とジョブ登録を担うサービス。

    メッセージ保存・ジョブ登録は同一トランザクションで行う。
    コマンドエラー（複数コマンド・未知コマンド）の場合は Slack にエラー通知する。
    """

    def __init__(
        self,
        db: Session,
        slack_client: SlackClient,
        plugin_loader: PluginLoader,
    ) -> None:
        self._db = db
        self._slack = slack_client
        self._plugins = plugin_loader

    def handle(
        self,
        *,
        channel_id: str,
        thread_ts: str | None,
        user: str,
        text: str,
        timestamp: str,
    ) -> None:
        """メッセージを処理する。

        1. テキストをコマンドパーサーに渡す
        2. メッセージを DB に保存する
        3a. コマンドなし  → 保存のみ
        3b. 複数コマンド  → 保存 + Slack エラー通知
        3c. 未知コマンド  → 保存 + Slack エラー通知
        3d. 既知コマンド  → 保存 + ジョブ登録

        Raises:
            Exception: DB 書き込み失敗時（保存・ジョブ双方ともロールバック）
        """
        thread_context = {
            "channel_id": channel_id,
            "thread_ts": thread_ts,
            "user": user,
        }

        # --- コマンド解析 ---
        error_text: str | None = None
        parsed = None
        try:
            parsed = parse_command(text)
        except MultipleCommandsError:
            error_text = "エラー: 1 つのメッセージに複数のコマンドが含まれています。"
        except CommandSyntaxError as exc:
            error_text = f"エラー: コマンドの解析に失敗しました。({exc})"

        if error_text is None and parsed is not None:
            if self._plugins.get(parsed.name) is None:
                error_text = f"エラー: 未知のコマンド `!{parsed.name}` です。"

        # --- メッセージ保存 ---
        message = Message(
            channel_id=channel_id,
            thread_ts=thread_ts,
            user=user,
            text=text,
            timestamp=timestamp,
        )
        self._db.add(message)

        # --- ジョブ登録（既知コマンドのみ） ---
        if error_text is None and parsed is not None:
            job = Job(
                command=parsed.name,
                args=json.dumps({"kwargs": parsed.kwargs, "args": parsed.args}),
                thread_context=thread_context,
                status=JobStatus.pending,
                trace_id=get_trace_id(),
            )
            self._db.add(job)

        try:
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

        # --- Slack エラー通知（コミット後） ---
        if error_text is not None:
            self._slack.post_message(
                channel=channel_id,
                thread_ts=thread_ts,
                text=error_text,
            )
