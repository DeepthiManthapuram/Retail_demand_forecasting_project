"""
logging_config.py
=================
Centralised logging configuration with read-only filesystem safety.
"""

import logging
import logging.handlers
import sys
import os
from pathlib import Path


_RESET = "\033[0m"
_COLOURS = {
    "DEBUG":    "\033[36m",
    "INFO":     "\033[32m",
    "WARNING":  "\033[33m",
    "ERROR":    "\033[31m",
    "CRITICAL": "\033[35m",
}


class _ColouredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        colour = _COLOURS.get(record.levelname, _RESET)
        record.levelname = f"{colour}{record.levelname:<8}{_RESET}"
        return super().format(record)


def setup_logging(
    log_level: str = "INFO",
    logs_dir: Path | None = None,
    log_to_file: bool = True,
) -> None:
    # Disable file logging on Vercel/serverless environments
    if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        log_to_file = False

    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    plain_fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(_ColouredFormatter(fmt=plain_fmt, datefmt=date_fmt))
    root_logger.addHandler(console_handler)

    # File handlers (safely wrapped)
    if log_to_file and logs_dir is not None:
        try:
            logs_dir = Path(logs_dir)
            logs_dir.mkdir(parents=True, exist_ok=True)

            log_files: list[tuple[str, str | None]] = [
                ("app",        None),
                ("api",        "backend"),
                ("training",   "training"),
                ("prediction", "prediction"),
                ("database",   "database"),
            ]

            for stem, name_prefix in log_files:
                file_handler = logging.handlers.RotatingFileHandler(
                    filename=logs_dir / f"{stem}.log",
                    maxBytes=10 * 1024 * 1024,
                    backupCount=5,
                    encoding="utf-8",
                )
                file_handler.setLevel(numeric_level)
                file_handler.setFormatter(logging.Formatter(fmt=plain_fmt, datefmt=date_fmt))

                if name_prefix is None:
                    root_logger.addHandler(file_handler)
                else:
                    named_logger = logging.getLogger(name_prefix)
                    named_logger.addHandler(file_handler)
        except Exception as exc:
            sys.stdout.write(f"File logging disabled: {exc}\n")

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
