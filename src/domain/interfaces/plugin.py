from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class CommandRegistry:
    command_name: str
    executable_path: str
    description: str


class BasePlugin(ABC):
    """Deprecated: Python class-based plugin interface.

    This placeholder remains for backward compatibility while the system
    migrates to shell command plugins. Remove after `src/infrastructure/plugin_loader.py`
    and related code are refactored to use `CommandRegistry`.
    """

    command_name: str
    description: str

    @abstractmethod
    def execute(
        self,
        kwargs: dict[str, str | bool],
        args: str,
        thread_context: dict,
    ) -> str: ...
