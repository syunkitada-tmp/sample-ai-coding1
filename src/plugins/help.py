from __future__ import annotations

from typing import TYPE_CHECKING

from src.domain.interfaces.plugin import BasePlugin

if TYPE_CHECKING:
    from src.infrastructure.plugin_loader import PluginLoader


class HelpPlugin(BasePlugin):
    """登録済みプラグインの一覧を返す組み込みコマンド。"""

    command_name = "help"
    description = "利用可能なコマンドの一覧を表示します"

    def __init__(self, plugin_loader: PluginLoader) -> None:
        self._loader = plugin_loader

    def execute(
        self,
        kwargs: dict[str, str | bool],
        args: str,
        thread_context: dict,
    ) -> str:
        commands = self._loader.list_commands()
        if not commands:
            return "利用可能なコマンドはありません。"

        lines = []
        for name in sorted(commands):
            plugin = self._loader.get(name)
            desc = plugin.description if plugin else ""
            lines.append(f"!{name}: {desc}")
        return "\n".join(lines)
