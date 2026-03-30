"""Logging configuration and trace_id context management."""

from __future__ import annotations

import logging
from contextvars import ContextVar

_trace_id_var: ContextVar[str] = ContextVar("trace_id", default="-")


def set_trace_id(value: str | None) -> None:
    """Set the trace_id for the current context. Pass None to reset to placeholder."""
    _trace_id_var.set(value if value is not None else "-")


def get_trace_id() -> str:
    """Return the current trace_id, or '-' if not set."""
    return _trace_id_var.get()


class TraceFilter(logging.Filter):
    """Inject trace_id into every LogRecord."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = get_trace_id()
        return True


_LOG_FORMAT = (
    "%(asctime)s %(levelname)s"
    " [%(filename)s:%(lineno)d]"
    " [trace_id=%(trace_id)s]"
    " %(name)s: %(message)s"
)


def configure_logging(level: int = logging.INFO) -> None:
    """Configure the root logger with TraceFilter and structured format.

    Safe to call multiple times — duplicate handlers are removed before adding.
    """
    root = logging.getLogger()
    root.setLevel(level)

    # Remove previously installed chatops handler to avoid duplicates
    root.handlers = [
        h
        for h in root.handlers
        if not any(isinstance(f, TraceFilter) for f in h.filters)
    ]

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.addFilter(TraceFilter())
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    root.addHandler(handler)
