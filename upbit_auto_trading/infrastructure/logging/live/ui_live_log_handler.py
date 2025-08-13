"""
UI Live Log Handler
====================

A lightweight in-memory publisher for log records to power real-time log viewers
without polling the log file. Follows Clean/DDD: Infrastructure provides the
handler and an in-memory buffer; Application (Presenter) drains it on a timer.
"""
from __future__ import annotations

import logging
import threading
from collections import deque
from typing import Deque, List, Optional, Tuple

try:
    import logging.handlers as logging_handlers  # type: ignore
except Exception:  # pragma: no cover
    logging_handlers = None  # type: ignore


class LiveLogBuffer:
    """Thread-safe ring buffer with monotonically increasing sequence IDs."""

    def __init__(self, max_lines: int = 5000) -> None:
        self._buf: Deque[Tuple[int, str]] = deque(maxlen=max_lines)
        self._lock = threading.Lock()
        self._next_seq: int = 1

    def append(self, line: str) -> int:
        with self._lock:
            seq = self._next_seq
            self._next_seq += 1
            self._buf.append((seq, line))
            return seq

    def get_since(self, last_seq: int) -> Tuple[List[str], int]:
        """Return lines with seq > last_seq and the highest seq observed.
        If last_seq is far behind window, returns all currently stored lines.
        """
        with self._lock:
            lines: List[str] = []
            max_seq = last_seq
            for seq, text in self._buf:
                if seq > last_seq:
                    lines.append(text)
                    if seq > max_seq:
                        max_seq = seq
            return lines, max_seq

    def clear(self) -> None:
        with self._lock:
            self._buf.clear()

    def last_seq(self) -> int:
        with self._lock:
            return self._next_seq - 1


_global_buffer: Optional[LiveLogBuffer] = None
_live_handler: Optional[UILiveLogHandler] = None  # type: ignore[name-defined]


def get_live_log_buffer() -> LiveLogBuffer:
    global _global_buffer
    if _global_buffer is None:
        _global_buffer = LiveLogBuffer()
    return _global_buffer


class UILiveLogHandler(logging.Handler):
    """A logging.Handler that formats records and publishes lines into LiveLogBuffer."""

    def __init__(self, buffer: Optional[LiveLogBuffer] = None, level: int = logging.NOTSET,
                 formatter: Optional[logging.Formatter] = None) -> None:
        super().__init__(level=level)
        self._buffer = buffer or get_live_log_buffer()
        if formatter is not None:
            self.setFormatter(formatter)

    def emit(self, record: logging.LogRecord) -> None:  # noqa: D401
        try:
            # Use handler's formatter if available; else fallback to a reasonable default
            formatter = self.formatter or _resolve_default_formatter()
            text = formatter.format(record)
            # Split on newlines to keep UI line semantics consistent
            for line in text.splitlines():
                if line.strip():
                    self._buffer.append(line)
        except Exception:
            # Handlers must not raise
            self.handleError(record)


def _resolve_default_formatter() -> logging.Formatter:
    """Try to reuse an existing handler's formatter; otherwise use a sane default."""
    # Prefer FileHandlers to mirror log file formatting if present
    try:
        root = logging.getLogger()
        candidates = list(root.handlers)
        # Include logging.root as well (defensive)
        candidates += list(logging.root.handlers)
        # Try to find a FileHandler with a formatter
        for h in candidates:
            try:
                if isinstance(h, logging.FileHandler) and h.formatter is not None:
                    return h.formatter
            except Exception:
                continue
        # Fallback to any handler with a formatter
        for h in candidates:
            try:
                if h.formatter is not None:
                    return h.formatter
            except Exception:
                continue
    except Exception:
        pass
    # Final fallback: bracketed timestamp with milliseconds and level/name
    # %(msecs) requires style '%%' and works with datefmt seconds resolution
    return logging.Formatter(
        fmt='[%(asctime)s.%(msecs)03d] [%(levelname)s] %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def attach_live_log_handler(level: int = logging.NOTSET) -> UILiveLogHandler:
    """Attach a singleton live log handler to the root logger if not present."""
    global _live_handler
    if _live_handler is not None:
        return _live_handler

    handler = UILiveLogHandler(buffer=get_live_log_buffer(), level=level,
                               formatter=_resolve_default_formatter())
    logging.getLogger().addHandler(handler)
    _live_handler = handler
    return handler


def detach_live_log_handler() -> None:
    """Detach the singleton live log handler from the root logger (if attached)."""
    global _live_handler
    if _live_handler is not None:
        try:
            logging.getLogger().removeHandler(_live_handler)
        except Exception:
            pass
        _live_handler = None
