from abc import ABC, abstractmethod


class BasePlugin(ABC):
    command_name: str
    description: str

    @abstractmethod
    def execute(
        self,
        kwargs: dict[str, str | bool],
        args: list[str],
        thread_context: dict,
    ) -> str: ...
