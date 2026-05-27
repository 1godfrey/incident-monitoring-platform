import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.database import get_db
from app.schemas import HealthCheckResponse, IncidentResponse, ServiceSummary, SummaryResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health/{service_id}", response_model=list[HealthCheckResponse])
async def get_service_health(
    service_id: int,
    limit: int = Query(default=100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Return the most recent health checks for a service (newest first).

    The `limit` parameter lets the dashboard fetch only what it will render,
    keeping response payloads small as check history accumulates.
    """
    service = await crud.get_service(db, service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service {service_id} not found.",
        )

    checks = await crud.get_health_checks_for_service(db, service_id, limit=limit)
    return checks


@router.get("/incidents", response_model=list[IncidentResponse])
async def get_incidents(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Return the most recent state-change alerts (DOWN / RECOVERED), newest first.

    These are the same events sent to Discord — persisted so the dashboard
    can display them without needing a Discord integration on the frontend.
    """
    return await crud.get_recent_incidents(db, limit=limit)


@router.get("/summary", response_model=SummaryResponse)
async def get_summary(
    window_hours: int = Query(default=24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    """Return uptime and latency summary for all services.

    `window_hours` defaults to 24h; the dashboard can request 7d (168h) for
    the weekly trend view without a separate endpoint.
    """
    stats = await crud.get_summary_stats(db, window_hours=window_hours)
    return SummaryResponse(services=[ServiceSummary(**s) for s in stats])
