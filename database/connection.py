"""
connection.py
=============
Database engine and session factory for the Retail Demand Forecasting app.

Supports both:
    - SQLite  (default, zero-config, for local development)
    - PostgreSQL via asyncpg (production, set DATABASE_URL env var)

Usage
-----
    from database.connection import get_db, engine
    from database.models import Base

    # Create tables (called on app startup)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Dependency injection in FastAPI route
    async def my_route(db: AsyncSession = Depends(get_db)):
        ...
"""

import sys
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# ---------------------------------------------------------------------------
# Resolve project root for imports
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from config.settings import get_settings
from config.logging_config import get_logger

logger = get_logger(__name__)


def _get_engine_kwargs(database_url: str) -> dict:
    """
    Build SQLAlchemy engine kwargs appropriate for the configured backend.

    SQLite requires special pool and thread-check settings when used in a
    multi-threaded FastAPI environment.

    Args:
        database_url: The full connection string.

    Returns:
        Dictionary of keyword arguments for create_engine().
    """
    if database_url.startswith("sqlite"):
        return {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
            "echo": False,
        }
    # PostgreSQL / MySQL — use standard connection pool
    return {
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
        "echo": False,
    }


# ---------------------------------------------------------------------------
# Build engine and session factory (synchronous — used throughout this app)
# ---------------------------------------------------------------------------
settings = get_settings()

_engine_kwargs = _get_engine_kwargs(settings.database_url)
engine = create_engine(settings.database_url, **_engine_kwargs)

# Enable WAL mode for SQLite (better concurrent read performance)
if settings.database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: ANN001
        """Enable Write-Ahead Logging for improved SQLite concurrency."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# Dependency — used in FastAPI routes via Depends(get_db)
# ---------------------------------------------------------------------------
def get_db():
    """
    Yield a database session and ensure it is closed after the request.

    Yields:
        SQLAlchemy Session object.
    """
    db: Session = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Table creation helper — called once on application startup
# ---------------------------------------------------------------------------
def create_all_tables() -> None:
    """
    Create all database tables defined in database/models.py.

    This is idempotent — it will not drop or modify existing tables.
    Safe to call on every startup.
    """
    # Import Base here to avoid circular imports
    from database.models import Base  # noqa: PLC0415

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created / verified successfully.")


def drop_all_tables() -> None:
    """
    Drop ALL database tables.  USE WITH EXTREME CAUTION.
    Intended for test teardown only.
    """
    from database.models import Base  # noqa: PLC0415

    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped.")
