"""Structured JSON logs.

Call configure_logging() once at startup. Then, in any module:

    log = structlog.get_logger()
    log.info("reply_completed", decision="ANSWER", duration_ms=840)

Bind ids once where a Kafka handler starts, and every line after carries them:

    structlog.contextvars.bind_contextvars(run_id=str(req.run_id), organization_id=...)

Never log message text, prompts or document content at INFO or above.
"""

import logging
import sys

import structlog


def configure_logging(level: str = "INFO", *, json: bool = True) -> None:
    level_number = logging.getLevelNamesMapping()[level.upper()]

    # Libraries (psycopg, aiokafka, httpx) use the standard logging module.
    # Send their output to stderr as plain lines, at WARNING and above only.
    logging.basicConfig(
        stream=sys.stderr, level=logging.WARNING, format="%(levelname)s %(name)s %(message)s"
    )

    renderer = structlog.processors.JSONRenderer() if json else structlog.dev.ConsoleRenderer()
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,  # adds run_id, organization_id, ...
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.format_exc_info,  # exception tracebacks as text
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level_number),
        logger_factory=structlog.PrintLoggerFactory(sys.stdout),
        cache_logger_on_first_use=True,
    )