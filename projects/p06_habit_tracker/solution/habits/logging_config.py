"""structlog setup: key=value lines on standard error, so standard output stays clean for results."""

import logging
import sys
from typing import Any, TextIO

import structlog


def configure_logging(*, verbose: bool = False, stream: TextIO | None = None) -> None:
    """Configure structlog to render ``key=value`` lines.

    Args:
        verbose: Show ``info`` events; otherwise only warnings and errors.
        stream: Where log lines go. By default ``sys.stderr`` is looked up at each log call, so the
            logger keeps working when the stream is swapped (as test frameworks do).
    """

    def logger_factory(*_args: Any) -> structlog.PrintLogger:
        return structlog.PrintLogger(stream or sys.stderr)

    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.KeyValueRenderer(key_order=["timestamp", "level", "event"], sort_keys=True),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO if verbose else logging.WARNING),
        logger_factory=logger_factory,
        cache_logger_on_first_use=False,
    )
