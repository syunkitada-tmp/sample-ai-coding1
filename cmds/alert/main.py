from __future__ import annotations

import sys

from cmds.lib.utils import exit_code, output_json, parse_args


def run(argv: list[str] | None = None) -> tuple[int, str]:
    """Execute the alert command logic and return exit code and output."""
    if argv is None:
        argv = sys.argv[1:]

    payload = parse_args(argv)
    host = payload["kwargs"].get("host")
    args = payload["args"]

    if not host:
        return exit_code(False), output_json({"error": "--host is required"})

    message = f"Alert for {host}"
    if args:
        message = f"{message} {args}"

    return exit_code(True), output_json({"result": message})


def main() -> None:
    code, output = run()
    print(output)
    raise SystemExit(code)
