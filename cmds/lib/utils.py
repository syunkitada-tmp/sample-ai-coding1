from __future__ import annotations

import json
from typing import Any


def parse_kwargs(argv: list[str]) -> tuple[dict[str, Any], str]:
    """Parse command-line style arguments into kwargs and positional args."""
    kwargs: dict[str, Any] = {}
    args: list[str] = []
    i = 0
    while i < len(argv):
        token = argv[i]
        if token.startswith("--"):
            key = token[2:]
            if not key:
                i += 1
                continue
            if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                kwargs[key] = argv[i + 1]
                i += 2
            else:
                kwargs[key] = True
                i += 1
        else:
            args.append(token)
            i += 1
    return kwargs, " ".join(args)


def parse_args(argv: list[str]) -> dict[str, Any]:
    """Parse raw argv into a structured payload for command execution."""
    kwargs, args = parse_kwargs(argv)
    return {"kwargs": kwargs, "args": args}


def output_json(data: dict[str, Any]) -> str:
    """Serialize data to JSON for command output."""
    return json.dumps(data, ensure_ascii=False)


def output_text(text: str) -> str:
    """Return plain text output for command output."""
    return text


def exit_code(success: bool = True) -> int:
    """Return the proper exit code for command execution."""
    return 0 if success else 1
