import importlib
import sys
import types
import pytest


@pytest.fixture
def loader():
    from src.infrastructure.plugin_loader import PluginLoader

    return PluginLoader()


def _make_plugin_module(name, command_name, description):
    """テスト用のインメモリプラグインモジュールを生成する"""
    from src.domain.interfaces.plugin import BasePlugin

    class DummyPlugin(BasePlugin):
        def execute(self, kwargs, args, thread_context):
            return "ok"

    DummyPlugin.command_name = command_name
    DummyPlugin.description = description

    mod = types.ModuleType(name)
    mod.DummyPlugin = DummyPlugin
    return mod


def test_register_and_get_plugin(loader):
    mod = _make_plugin_module("plugins.alert", "alert", "Alert command")
    loader.register_from_module(mod)
    plugin = loader.get("alert")
    assert plugin is not None
    assert plugin.command_name == "alert"


def test_get_unknown_plugin_returns_none(loader):
    assert loader.get("unknown") is None


def test_list_all_commands(loader):
    mod1 = _make_plugin_module("plugins.alert", "alert", "Alert")
    mod2 = _make_plugin_module("plugins.help", "help", "Help")
    loader.register_from_module(mod1)
    loader.register_from_module(mod2)
    commands = loader.list_commands()
    assert "alert" in commands
    assert "help" in commands


def test_plugin_missing_command_name_is_skipped(loader, caplog):
    from src.domain.interfaces.plugin import BasePlugin

    class BadPlugin(BasePlugin):
        description = "no command_name"

        def execute(self, kwargs, args, thread_context):
            return "ok"

    mod = types.ModuleType("plugins.bad")
    mod.BadPlugin = BadPlugin
    loader.register_from_module(mod)
    assert loader.get("") is None
    assert len(loader.list_commands()) == 0


def test_plugin_missing_description_is_skipped(loader, caplog):
    from src.domain.interfaces.plugin import BasePlugin

    class BadPlugin(BasePlugin):
        command_name = "bad"

        def execute(self, kwargs, args, thread_context):
            return "ok"

    mod = types.ModuleType("plugins.bad2")
    mod.BadPlugin = BadPlugin
    loader.register_from_module(mod)
    assert loader.get("bad") is None


def test_plugin_missing_execute_is_skipped(loader):
    from src.domain.interfaces.plugin import BasePlugin

    class BadPlugin(BasePlugin):
        command_name = "bad"
        description = "missing execute"

    mod = types.ModuleType("plugins.bad3")
    mod.BadPlugin = BadPlugin
    loader.register_from_module(mod)
    assert loader.get("bad") is None


def test_reload_removes_unregistered_plugin(loader, tmp_path):
    """プラグインファイルを削除して reload すると消えることを確認"""
    mod = _make_plugin_module("plugins.alert", "alert", "Alert")
    loader.register_from_module(mod)
    assert loader.get("alert") is not None

    # plugin_dir からリロード（空ディレクトリ = プラグインなし）
    loader.reload(str(tmp_path))
    assert loader.get("alert") is None
