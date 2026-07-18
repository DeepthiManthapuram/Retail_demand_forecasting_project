"""
connection.py
=============
Database engine and session factory for the Retail Demand Forecasting app.
Auto-configures writeable SQLite database in Vercel/serverless environments.
"""

import sys
import os
import tempfile
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from config.settings import get_settings
from config.logging_config import get_logger

logger = get_logger(__name__)

settings = get_settings()

# Determine database URL — fallback to writeable /tmp/ in Vercel/Serverless
db_url = settings.database_url
if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    tmp_path = Path(tempfile.gettempdir()) / "retail_demand.db"
    db_url = f"sqlite:///{tmp_path}"
    logger.info("Serverless environment detected — using writeable DB at %s", tmp_path)


def _get_engine_kwargs(database_url: str) -> dict:
    if database_url.startswith("sqlite"):
        return {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
            "echo": False,
        }
    return {
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
        "echo": False,
    }


_engine_kwargs = _get_engine_kwargs(db_url)
engine = create_engine(db_url, **_engine_kwargs)

if db_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

_TABLES_INITIALIZED = False


def create_all_tables() -> None:
    """Create all database tables defined in database/models.py."""
    from database.models import Base  # noqa: PLC0415
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created / verified successfully.")


def drop_all_tables() -> None:
    from database.models import Base  # noqa: PLC0415
    Base.metadata.drop_all(bind=engine)


def get_db():
    """Yield a database session and ensure tables exist on serverless."""
    global _TABLES_INITIALIZED
    if not _TABLES_INITIALIZED:
        try:
            from database.models import Base  # noqa: PLC0415
            Base.metadata.create_all(bind=engine)
            _TABLES_INITIALIZED = True
        except Exception as exc:
            logger.warning("Table initialization notice: %s", exc)

    db: Session = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
