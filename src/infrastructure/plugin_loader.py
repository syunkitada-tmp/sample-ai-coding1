from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path
from types import ModuleType

from src.domain.interfaces.plugin import BasePlugin

logger = logging.getLogger(__name__)

_REQUIRED_FIELDS = ("command_name", "description")


def _is_valid_plugin(cls: type) -> bool:
    """BasePlugin のサブクラスかつ必須フィールドと execute が実装されているか検証する"""
    if not (
        isinstance(cls, type) and issubclass(cls, BasePlugin) and cls is not BasePlugin
    ):
        return False
    for field in _REQUIRED_FIELDS:
        if not getattr(cls, field, None):
            logger.warning(
                "Plugin %s is missing required field '%s', skipping.",
                cls.__name__,
                field,
            )
            return False
    if not callable(getattr(cls, "execute", None)):
        logger.warning("Plugin %s is missing 'execute' method, skipping.", cls.__name__)
        return False
    # abstractmethod が残っていたら未実装とみなす
    if getattr(cls.execute, "__isabstractmethod__", False):
        logger.warning(
            "Plugin %s has not implemented 'execute', skipping.", cls.__name__
        )
        return False
    return True


class PluginLoader:
    def __init__(self) -> None:
        self._registry: dict[str, BasePlugin] = {}

    def register_from_module(self, module: ModuleType) -> None:
        """モジュール内の有効なプラグインクラスを登録する"""
        for attr_name in dir(module):
            cls = getattr(module, attr_name)
            if _is_valid_plugin(cls):
                instance = cls()
                self._registry[instance.command_name] = instance
                logger.info("Registered plugin: %s", instance.command_name)

    def reload(self, plugin_dir: str) -> None:
        """プラグインディレクトリを再スキャンしてレジストリを再構築する"""
        self._registry.clear()
        self.load_from_dir(plugin_dir)

    def load_from_dir(self, plugin_dir: str) -> None:
        """ディレクトリ内の .py ファイルをスキャンしてプラグインを登録する"""
        base_path = Path(plugin_dir)
        if not base_path.exists():
            logger.warning("Plugin directory '%s' does not exist.", plugin_dir)
            return

        for py_file in sorted(base_path.glob("*.py")):
            if py_file.name.startswith("_"):
                continue
            module_name = f"_chatops_plugin_{py_file.stem}"
            spec = importlib.util.spec_from_file_location(module_name, py_file)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            try:
                spec.loader.exec_module(module)
                self.register_from_module(module)
            except Exception as exc:
                logger.error("Failed to load plugin '%s': %s", py_file.name, exc)

    def get(self, command_name: str) -> BasePlugin | None:
        return self._registry.get(command_name)

    def list_commands(self) -> dict[str, str]:
        """登録済みコマンド名と説明の辞書を返す"""
        return {name: plugin.description for name, plugin in self._registry.items()}
