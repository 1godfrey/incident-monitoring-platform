import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.logging_config import setup_logging
from app.routes import health as health_router
from app.routes import services as services_router
from app.scheduler.jobs import run_monitoring_cycle

setup_logging()
logger = logging.getLogger(__name__)

# APScheduler instance; lives for the lifetime of the process.
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown of long-lived resources.

    Using lifespan rather than @app.on_event keeps the startup/shutdown
    contract explicit and is the recommended FastAPI pattern as of 0.93+.
    """
    logger.info("startup_begin")

    # 1. Ensure DB tables exist (idempotent)
    await init_db()
    logger.info("database_ready")

    # 2. Start the monitoring scheduler
    scheduler.add_job(
        run_monitoring_cycle,
        trigger="interval",
        seconds=settings.check_interval_seconds,
        id="monitoring_cycle",
        max_instances=1,       # prevents overlap if a cycle takes longer than the interval
        misfire_grace_time=30, # tolerate brief scheduler hiccups without skipping checks
    )
    scheduler.start()
    logger.info(
        "scheduler_started",
        extra={"interval_seconds": settings.check_interval_seconds},
    )

    yield  # application runs here

    # Graceful shutdown: drain in-flight checks before the process exits
    scheduler.shutdown(wait=True)
    logger.info("scheduler_stopped")


app = FastAPI(
    title="Incident Monitoring Platform",
    description="Lightweight uptime and latency monitoring for SRE portfolios.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS: allow all origins for the MVP dashboard; tighten to specific origins
# (e.g. the Vite dev server and prod CDN URL) before any public deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://incident-monitoring-platform.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(services_router.router)
app.include_router(health_router.router)


@app.get("/", tags=["meta"])
async def root():
    return {"status": "ok", "service": "incident-monitoring-platform"}
