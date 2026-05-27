from datetime import datetime, timedelta, timezone

from sqlalchemy import Integer, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import HealthCheck, Incident, MonitoredService
from app.schemas import ServiceCreate


# ── Services ─────────────────────────────────────────────────────────────────

async def get_all_services(db: AsyncSession) -> list[MonitoredService]:
    result = await db.execute(select(MonitoredService).order_by(MonitoredService.id))
    return result.scalars().all()


async def get_service(db: AsyncSession, service_id: int) -> MonitoredService | None:
    return await db.get(MonitoredService, service_id)


async def create_service(db: AsyncSession, data: ServiceCreate) -> MonitoredService:
    service = MonitoredService(
        name=data.name,
        url=str(data.url),
        json_path=data.json_path,
        expected_value=data.expected_value,
    )
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service


# ── Health Checks ─────────────────────────────────────────────────────────────

async def create_health_check(
    db: AsyncSession,
    service_id: int,
    status_code: int | None,
    response_time_ms: float,
    success: bool,
) -> HealthCheck:
    check = HealthCheck(
        service_id=service_id,
        status_code=status_code,
        response_time_ms=response_time_ms,
        success=success,
    )
    db.add(check)
    await db.commit()
    await db.refresh(check)
    return check


async def get_health_checks_for_service(
    db: AsyncSession, service_id: int, limit: int = 100
) -> list[HealthCheck]:
    """Return the most recent `limit` checks for a service, newest first."""
    result = await db.execute(
        select(HealthCheck)
        .where(HealthCheck.service_id == service_id)
        .order_by(HealthCheck.checked_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


# ── Incidents ─────────────────────────────────────────────────────────────────

async def create_incident(
    db: AsyncSession,
    service: MonitoredService,
    status: str,
    http_status_code: int | None,
    response_time_ms: float,
    content_detail: str | None,
) -> Incident:
    incident = Incident(
        service_id=service.id,
        service_name=service.name,
        service_url=str(service.url),
        status=status,
        http_status_code=http_status_code,
        response_time_ms=response_time_ms,
        content_detail=content_detail,
    )
    db.add(incident)
    await db.commit()
    await db.refresh(incident)
    return incident


async def get_recent_incidents(db: AsyncSession, limit: int = 50) -> list[Incident]:
    """Return the most recent `limit` incidents across all services, newest first."""
    result = await db.execute(
        select(Incident).order_by(Incident.triggered_at.desc()).limit(limit)
    )
    return result.scalars().all()


async def get_summary_stats(
    db: AsyncSession, window_hours: int = 24
) -> list[dict]:
    """Aggregate uptime and latency per service over the given time window.

    Runs a single grouped query rather than N per-service queries — important
    when the number of monitored services grows.
    """
    since = datetime.now(timezone.utc) - timedelta(hours=window_hours)

    # Subquery: last check timestamp per service
    last_check_sq = (
        select(
            HealthCheck.service_id,
            func.max(HealthCheck.checked_at).label("last_checked_at"),
        )
        .group_by(HealthCheck.service_id)
        .subquery()
    )

    # Main aggregation query
    result = await db.execute(
        select(
            MonitoredService.id,
            MonitoredService.name,
            MonitoredService.url,
            func.count(HealthCheck.id).label("total_checks"),
            func.sum(HealthCheck.success.cast(Integer)).label("success_count"),
            func.avg(HealthCheck.response_time_ms).label("avg_response_time_ms"),
            last_check_sq.c.last_checked_at,
        )
        .outerjoin(
            HealthCheck,
            (HealthCheck.service_id == MonitoredService.id)
            & (HealthCheck.checked_at >= since),
        )
        .outerjoin(last_check_sq, last_check_sq.c.service_id == MonitoredService.id)
        .group_by(
            MonitoredService.id,
            MonitoredService.name,
            MonitoredService.url,
            last_check_sq.c.last_checked_at,
        )
        .order_by(MonitoredService.id)
    )

    rows = result.mappings().all()
    stats = []
    for row in rows:
        total = row["total_checks"] or 0
        successes = int(row["success_count"] or 0)
        uptime = round((successes / total * 100), 2) if total > 0 else 0.0
        stats.append(
            {
                "service_id": row["id"],
                "service_name": row["name"],
                "service_url": row["url"],
                "total_checks": total,
                "uptime_percentage": uptime,
                "avg_response_time_ms": round(row["avg_response_time_ms"] or 0.0, 2),
                "last_checked_at": row["last_checked_at"],
            }
        )
    return stats

