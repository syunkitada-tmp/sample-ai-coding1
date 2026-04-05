from dataclasses import dataclass


@dataclass(frozen=True)
class CommandRegistry:
    command_name: str
    executable_path: str
    description: str
