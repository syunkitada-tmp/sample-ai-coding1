from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path

from src.domain.interfaces.plugin import CommandRegistry

logger = logging.getLogger(__name__)


def _is_chatops_executable(path: Path) -> bool:
    return (
        path.is_file() and os.access(path, os.X_OK) and path.name.startswith("chatops-")
    )


def _command_name_from_path(path: Path) -> str:
    return path.name[len("chatops-") :]


class PluginLoader:
    def __init__(self) -> None:
        self._registry: dict[str, CommandRegistry] = {}

    def register_command(self, command: CommandRegistry) -> None:
        """PATH ベースの chatops-* コマンドを登録する"""
        self._registry[command.command_name] = command
        logger.info("Registered command: %s", command.command_name)

    def reload(self) -> None:
        """レジストリを再構築する（PATH スキャンのみ）"""
        self._registry.clear()
        self.load_from_path()

    def load_from_path(self, path_env: str | None = None) -> None:
        """PATH をスキャンして chatops-* コマンドを登録する"""
        path_value = path_env if path_env is not None else os.environ.get("PATH", "")
        if not path_value:
            return

        seen: set[str] = set()
        for entry in path_value.split(os.pathsep):
            if not entry:
                continue
            directory = Path(entry)
            if not directory.is_dir():
                continue
            try:
                for candidate in sorted(directory.iterdir()):
                    if not _is_chatops_executable(candidate):
                        continue
                    command_name = _command_name_from_path(candidate)
                    if command_name in seen:
                        continue
                    resolved = shutil.which(candidate.name, path=path_value)
                    executable_path = str(
                        Path(resolved) if resolved is not None else candidate
                    )
                    self.register_command(
                        CommandRegistry(
                            command_name=command_name,
                            executable_path=executable_path,
                            description="No description available",
                        )
                    )
                    seen.add(command_name)
            except PermissionError:
                logger.warning("Permission denied accessing directory: %s", directory)
                continue

    def get(self, command_name: str) -> CommandRegistry | None:
        return self._registry.get(command_name)

    def list_commands(self) -> dict[str, str]:
        """登録済みコマンド名と説明の辞書を返す"""
        return {name: cmd.description for name, cmd in self._registry.items()}
