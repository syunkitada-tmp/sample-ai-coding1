"""Tests for src/lib/logging.py — configure_logging / trace_id management."""

from __future__ import annotations

import logging

import pytest

from src.lib.logging import (
    TraceFilter,
    configure_logging,
    get_trace_id,
    set_trace_id,
)


class TestTraceIdContext:
    def test_default_returns_placeholder(self):
        set_trace_id(None)
        assert get_trace_id() == "-"

    def test_set_and_get(self):
        set_trace_id("abc-123")
        assert get_trace_id() == "abc-123"

    def test_reset_to_placeholder(self):
        set_trace_id("abc-123")
        set_trace_id(None)
        assert get_trace_id() == "-"


class TestTraceFilter:
    def _make_record(self) -> logging.LogRecord:
        return logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/some/path/myfile.py",
            lineno=42,
            msg="hello",
            args=(),
            exc_info=None,
        )

    def test_filter_injects_trace_id(self):
        set_trace_id("xyz-999")
        f = TraceFilter()
        record = self._make_record()
        f.filter(record)
        assert record.trace_id == "xyz-999"

    def test_filter_injects_placeholder_when_no_trace_id(self):
        set_trace_id(None)
        f = TraceFilter()
        record = self._make_record()
        f.filter(record)
        assert record.trace_id == "-"

    def test_filter_returns_true(self):
        f = TraceFilter()
        record = self._make_record()
        assert f.filter(record) is True


class TestConfigureLogging:
    def test_root_logger_has_handler_after_configure(self):
        # configure_logging を複数回呼んでも重複 handler が増えないこと
        configure_logging()
        configure_logging()
        root = logging.getLogger()
        trace_handlers = [
            h
            for h in root.handlers
            if any(isinstance(f, TraceFilter) for f in h.filters)
        ]
        assert len(trace_handlers) == 1

    def test_log_record_contains_trace_id_in_format(self, caplog):
        set_trace_id("test-tid")
        configure_logging(level=logging.DEBUG)
        with caplog.at_level(logging.INFO, logger="test_format"):
            logger = logging.getLogger("test_format")
            logger.info("check format")
        # caplog が trace_id 付きレコードを持つことを確認
        assert any(
            hasattr(r, "trace_id") and r.trace_id == "test-tid" for r in caplog.records
        )
