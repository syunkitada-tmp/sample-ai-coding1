import pytest
from unittest.mock import MagicMock


def _make_loader(commands: dict[str, str]):
    """コマンド名→説明 の辞書からモック PluginLoader を生成する"""
    loader = MagicMock()
    loader.list_commands.return_value = list(commands.keys())

    def _get(name):
        if name in commands:
            p = MagicMock()
            p.command_name = name
            p.description = commands[name]
            return p
        return None

    loader.get.side_effect = _get
    return loader


class TestHelpPlugin:

    def test_returns_command_list(self):
        """登録済みコマンドを !cmd: 説明 で返す"""
        from src.plugins.help import HelpPlugin

        loader = _make_loader({"alert": "Analyze alert logs", "deploy": "Deploy app"})
        plugin = HelpPlugin(plugin_loader=loader)
        result = plugin.execute(kwargs={}, args=[], thread_context={})
        assert "!alert: Analyze alert logs" in result
        assert "!deploy: Deploy app" in result

    def test_reply_format_one_per_line(self):
        """各コマンドが改行で区切られる"""
        from src.plugins.help import HelpPlugin

        loader = _make_loader({"alert": "Analyze alert logs", "deploy": "Deploy app"})
        plugin = HelpPlugin(plugin_loader=loader)
        result = plugin.execute(kwargs={}, args=[], thread_context={})
        lines = result.strip().splitlines()
        assert len(lines) == 2

    def test_no_plugins_returns_empty_message(self):
        """プラグインが0件なら専用メッセージを返す"""
        from src.plugins.help import HelpPlugin

        loader = _make_loader({})
        plugin = HelpPlugin(plugin_loader=loader)
        result = plugin.execute(kwargs={}, args=[], thread_context={})
        assert "利用可能なコマンドはありません" in result

    def test_command_name_and_description(self):
        """command_name と description が定義されている"""
        from src.plugins.help import HelpPlugin

        loader = _make_loader({})
        plugin = HelpPlugin(plugin_loader=loader)
        assert plugin.command_name == "help"
        assert plugin.description != ""
