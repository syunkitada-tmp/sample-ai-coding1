from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Depends
from sqlalchemy.orm import Session

from src.config import settings
from src.infrastructure.db import get_db
from src.infrastructure.slack_client import SlackClient
from src.infrastructure.plugin_loader import PluginLoader
from src.domain.services.message_service import MessageService
from src.plugins.help import HelpPlugin

if TYPE_CHECKING:
    pass

# シングルトンのプラグインローダー（アプリ起動時に一度だけ初期化）
_plugin_loader = PluginLoader()
_plugin_loader.load_from_dir(settings.plugin_dir)
# HelpPlugin は plugin_loader をコンストラクタ引数に取るため手動登録
_plugin_loader._registry["help"] = HelpPlugin(plugin_loader=_plugin_loader)


def get_slack_client() -> SlackClient:
    return SlackClient(proxy_url=settings.slack_proxy_url)


def get_plugin_loader() -> PluginLoader:
    return _plugin_loader


def get_message_service(
    db: Session = Depends(get_db),
    slack_client: SlackClient = Depends(get_slack_client),
    plugin_loader: PluginLoader = Depends(get_plugin_loader),
) -> MessageService:
    return MessageService(db=db, slack_client=slack_client, plugin_loader=plugin_loader)
