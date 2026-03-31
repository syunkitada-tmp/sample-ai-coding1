"""Slack proxy debug server.

A lightweight stub that mimics the Slack posting proxy API.
Receives POST /post requests, prints the payload to stdout,
and returns {"ok": true}.

Usage:
    python tools/slack_proxy_debug.py        # listens on port 8081
    PORT=9000 python tools/slack_proxy_debug.py
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


class DebugProxyHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path != "/post":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return

        print(json.dumps(payload, ensure_ascii=False, indent=2), flush=True)

        response = json.dumps({"ok": True}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, fmt: str, *args: object) -> None:  # noqa: D102
        print(f"[slack_proxy_debug] {fmt % args}", flush=True)


def main() -> None:
    port = int(os.environ.get("PORT", 8081))
    server = HTTPServer(("0.0.0.0", port), DebugProxyHandler)
    print(f"[slack_proxy_debug] listening on port {port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
