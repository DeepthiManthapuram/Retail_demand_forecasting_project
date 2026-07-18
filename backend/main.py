"""
main.py  (FastAPI application entry-point)
==========================================
Creates and configures the FastAPI application.

On startup the app:
    1. Sets up logging
    2. Creates database tables
    3. Seeds master data (stores + products)
    4. Generates the synthetic dataset (if not present)
    5. Returns system-ready status via GET /health

All API routes are registered via routers mounted to this app.
"""
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from config.settings import get_settings
from config.logging_config import setup_logging, get_logger
from database.connection import create_all_tables
from backend.routers import health, forecast, dataset, training, dashboard, models_router, reports

# ---------------------------------------------------------------------------
# Lifespan: startup and shutdown logic
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.

    Everything before 'yield' runs on startup;
    everything after runs on shutdown.
    """
    settings = get_settings()
    setup_logging(
        log_level=settings.log_level,
        logs_dir=settings.logs_dir,
        log_to_file=settings.log_to_file,
    )
    logger = get_logger("backend.main")
    logger.info("=" * 60)
    logger.info("  %s  v%s  starting …", settings.app_name, settings.app_version)
    logger.info("  Environment : %s", settings.environment)
    logger.info("  Database URL: %s", settings.database_url)
    logger.info("=" * 60)

    is_serverless = (
        os.environ.get("VERCEL")
        or "AWS_LAMBDA_FUNCTION_NAME" in os.environ
        or "LAMBDA_TASK_ROOT" in os.environ
        or str(Path.cwd()).startswith("/var/task")
        or str(Path(__file__)).startswith("/var/task")
    )

    # ---- Create DB tables & Seed (Local only to prevent serverless lifespan timeouts) ----
    if not is_serverless:
        try:
            create_all_tables()
            logger.info("✓ Database tables ready.")
        except Exception as exc:
            logger.error("✗ Database setup failed: %s", exc)

        try:
            from database.seed import run_seed
            run_seed()
            logger.info("✓ Master data seeded.")
        except Exception as exc:
            logger.warning("Seed step encountered an issue: %s", exc)
    else:
        logger.info("✓ Serverless lifespan — skipping DB initialization (database file copied on demand).")

    # ---- Generate synthetic dataset if missing (local environment only) ----
    if not is_serverless:
        synthetic_path = settings.datasets_dir / "synthetic_train.csv"
        kaggle_path    = settings.datasets_dir / "train.csv"
        if not synthetic_path.exists() and not kaggle_path.exists():
            try:
                logger.info("No dataset found — generating synthetic dataset …")
                from datasets.generate_dataset import main as gen_main
                gen_main()
                logger.info("✓ Synthetic dataset generated.")
            except Exception as exc:
                logger.error("Dataset generation failed: %s", exc)
    else:
        logger.info("✓ Serverless environment — skipping disk dataset generation.")

    logger.info("✓ System ready — listening on %s:%d", settings.api_host, settings.api_port)
    yield
    logger.info("Application shutting down.")


# ---------------------------------------------------------------------------
# Create FastAPI app
# ---------------------------------------------------------------------------
def create_app() -> FastAPI:
    """
    Factory function that builds and configures the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Production-grade retail demand forecasting API. "
            "Supports 500 Store×Item time series with multiple ML/DL models."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ---- CORS ----
    app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

    # ---- Routers ----
    app.include_router(health.router,          tags=["Health"])
    app.include_router(forecast.router,        prefix="/api",        tags=["Forecast"])
    app.include_router(dataset.router,         prefix="/api",        tags=["Dataset"])
    app.include_router(training.router,        prefix="/api",        tags=["Training"])
    app.include_router(dashboard.router,       prefix="/api",        tags=["Dashboard"])
    app.include_router(models_router.router,   prefix="/api",        tags=["Models"])
    app.include_router(reports.router,         prefix="/api",        tags=["Reports"])

    # ---- Global exception handler ----
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """Catch-all for unhandled exceptions; returns a JSON error response."""
        logger = get_logger("backend.main")
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred.", "error": str(exc)},
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
