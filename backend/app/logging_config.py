import logging
import sys
from pythonjsonlogger import jsonlogger

from app.config import settings


def setup_logging() -> None:
    """Configure structured JSON logging for production observability.

    JSON logs integrate directly with log aggregators (Datadog, Loki, CloudWatch).
    Each log line is a parseable object, making log-based alerting straightforward.
    """
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(settings.log_level.upper())

    # Suppress noisy third-party loggers in production
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
