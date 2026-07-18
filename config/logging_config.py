"""
logging_config.py
=================
Centralised logging configuration for the entire application.
Sets up rotating file handlers + coloured console output.
Import and call setup_logging() once at application startup.
"""

import logging
import logging.handlers
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# ANSI colour codes for console output
# ---------------------------------------------------------------------------
_RESET = "\033[0m"
_COLOURS = {
    "DEBUG":    "\033[36m",   # Cyan
    "INFO":     "\033[32m",   # Green
    "WARNING":  "\033[33m",   # Yellow
    "ERROR":    "\033[31m",   # Red
    "CRITICAL": "\033[35m",   # Magenta
}


class _ColouredFormatter(logging.Formatter):
    """
    Custom formatter that adds ANSI colour codes to log level names
    when writing to the console.  File handlers use the plain formatter.
    """

    def format(self, record: logging.LogRecord) -> str:
        colour = _COLOURS.get(record.levelname, _RESET)
        record.levelname = f"{colour}{record.levelname:<8}{_RESET}"
        return super().format(record)


def setup_logging(
    log_level: str = "INFO",
    logs_dir: Path | None = None,
    log_to_file: bool = True,
) -> None:
    """
    Configure the root logger with console and (optionally) rotating file handlers.

    Args:
        log_level:   Minimum severity level to capture (DEBUG, INFO, WARNING, …).
        logs_dir:    Directory where log files are written.
        log_to_file: When False only the console handler is attached.
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Plain format for files; coloured format for console
    plain_fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove any handlers added by previous calls (e.g. during tests)
    root_logger.handlers.clear()

    # ------------------------------------------------------------------
    # Console handler
    # ------------------------------------------------------------------
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(
        _ColouredFormatter(fmt=plain_fmt, datefmt=date_fmt)
    )
    root_logger.addHandler(console_handler)

    # ------------------------------------------------------------------
    # Rotating file handlers (one per module group)
    # ------------------------------------------------------------------
    if log_to_file and logs_dir is not None:
        logs_dir = Path(logs_dir)
        logs_dir.mkdir(parents=True, exist_ok=True)

        # (log_file_stem, logger_name_prefix)
        log_files: list[tuple[str, str | None]] = [
            ("app",        None),         # root / application
            ("api",        "backend"),    # FastAPI routers
            ("training",   "training"),   # training pipeline
            ("prediction", "prediction"), # prediction pipeline
            ("database",   "database"),   # database layer
        ]

        for stem, name_prefix in log_files:
            file_handler = logging.handlers.RotatingFileHandler(
                filename=logs_dir / f"{stem}.log",
                maxBytes=10 * 1024 * 1024,   # 10 MB per file
                backupCount=5,
                encoding="utf-8",
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(
                logging.Formatter(fmt=plain_fmt, datefmt=date_fmt)
            )

            if name_prefix is None:
                root_logger.addHandler(file_handler)
            else:
                named_logger = logging.getLogger(name_prefix)
                named_logger.addHandler(file_handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logging.info("Logging initialised — level=%s, file=%s", log_level, log_to_file)


def get_logger(name: str) -> logging.Logger:
    """
    Convenience factory — returns a named logger.

    Args:
        name: Typically __name__ of the calling module.

    Returns:
        A Logger instance scoped to the given name.
    """
    return logging.getLogger(name)
