from __future__ import annotations

import os
import sys
from pathlib import Path

from cmds.lib.utils import exit_code


DEFAULT_DESCRIPTIONS: dict[str, str] = {
    "alert": "Dummy alert command for triggering alerts.",
    "help": "List available chatops commands.",
}


def _is_chatops_command(path: Path) -> bool:
    return (
        path.is_file() and os.access(path, os.X_OK) and path.name.startswith("chatops-")
    )


def _command_name_from_path(path: Path) -> str:
    return path.name[len("chatops-") :]


def _scan_path_for_commands(path_env: str | None = None) -> dict[str, Path]:
    path_value = path_env if path_env is not None else os.environ.get("PATH", "")
    commands: dict[str, Path] = {}
    for entry in path_value.split(os.pathsep):
        if not entry:
            continue
        directory = Path(entry)
        if not directory.is_dir():
            continue
        for candidate in sorted(directory.iterdir()):
            if _is_chatops_command(candidate):
                name = _command_name_from_path(candidate)
                if name not in commands:
                    commands[name] = candidate
    return commands


def _describe_command(name: str) -> str:
    return DEFAULT_DESCRIPTIONS.get(name, "No description available")


def _format_help_output(commands: dict[str, Path]) -> str:
    if not commands:
        return "No commands are available."

    lines = []
    for name in sorted(commands):
        description = _describe_command(name)
        lines.append(f"!{name}: {description}")
    return "\n".join(lines)


def run(argv: list[str] | None = None) -> tuple[int, str]:
    if argv is None:
        argv = sys.argv[1:]

    commands = _scan_path_for_commands(os.environ.get("PATH"))
    output = _format_help_output(commands)
    return exit_code(True), output


def main() -> None:
    code, output = run()
    print(output)
    raise SystemExit(code)
