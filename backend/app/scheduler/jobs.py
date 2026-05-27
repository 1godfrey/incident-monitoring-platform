import logging
import time
from typing import Any

import httpx
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app import crud
from app.models import HealthCheck, MonitoredService

logger = logging.getLogger(__name__)

# In-memory map of service_id → last known success state.
# Used to fire Discord alerts only on state *transitions* (up→down, down→up)
# rather than every failed check, preventing notification spam.
_last_state: dict[int, bool] = {}

# Single shared httpx client reused across checks to benefit from connection pooling.
# Timeout is intentionally short: a 10s hang is itself a SLO violation worth flagging.
_http_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0),
            follow_redirects=True,
        )
    return _http_client


def _resolve_json_path(data: Any, path: str) -> Any:
    """Walk a dot-notation path through a nested dict.

    e.g. "status.indicator" on {"status": {"indicator": "none"}} → "none"
    Raises KeyError/TypeError if the path doesn't exist.
    """
    for key in path.split("."):
        data = data[key]
    return data


async def check_service(service: MonitoredService) -> dict[str, Any]:
    """Probe a single service and return raw result dict.

    Two-stage check:
      1. HTTP: status code < 400 → pass
      2. Content (optional): if json_path + expected_value are configured,
         parse the JSON body and compare the resolved value. A mismatch marks
         the check failed even when HTTP returned 200 — essential for status-
         page APIs like GitHub's that always return 200 but embed the real
         health state in a JSON field.
    """
    client = get_http_client()
    start = time.monotonic()
    try:
        response = await client.get(str(service.url))
        elapsed_ms = (time.monotonic() - start) * 1000
        success = response.status_code < 400
        content_detail: str | None = None

        if success and service.json_path and service.expected_value:
            try:
                body = response.json()
                actual = _resolve_json_path(body, service.json_path)
                if str(actual).lower() != service.expected_value.lower():
                    success = False
                    content_detail = (
                        f"`{service.json_path}` = **'{actual}'** "
                        f"(expected **'{service.expected_value}'**)"
                    )
                    logger.warning(
                        "content_check_failed",
                        extra={
                            "service_id": service.id,
                            "json_path": service.json_path,
                            "actual": actual,
                            "expected": service.expected_value,
                        },
                    )
            except (KeyError, TypeError) as exc:
                success = False
                content_detail = f"could not read `{service.json_path}`: {exc}"
                logger.warning(
                    "content_check_parse_error",
                    extra={"service_id": service.id, "error": str(exc)},
                )

        return {
            "status_code": response.status_code,
            "response_time_ms": round(elapsed_ms, 2),
            "success": success,
            "content_detail": content_detail,
        }
    except httpx.TimeoutException:
        elapsed_ms = (time.monotonic() - start) * 1000
        logger.warning("check_timeout", extra={"service_id": service.id, "url": service.url})
        return {"status_code": None, "response_time_ms": round(elapsed_ms, 2), "success": False, "content_detail": None}
    except httpx.RequestError as exc:
        elapsed_ms = (time.monotonic() - start) * 1000
        logger.warning(
            "check_error",
            extra={"service_id": service.id, "url": service.url, "error": str(exc)},
        )
        return {"status_code": None, "response_time_ms": round(elapsed_ms, 2), "success": False, "content_detail": None}


async def maybe_alert_discord(service: MonitoredService, result: dict[str, Any]) -> None:
    """Send a Discord webhook message when a service changes state.

    Only fires on transitions to avoid alert fatigue — a core SRE principle.
    """
    if not settings.discord_webhook_url:
        return

    current_success = result["success"]
    previous_success = _last_state.get(service.id)

    if previous_success is None:
        # First check for this service — establish baseline, no alert yet
        _last_state[service.id] = current_success
        return

    if current_success == previous_success:
        return  # no state change

    _last_state[service.id] = current_success

    if current_success:
        color = 3066993  # green
        status_text = "RECOVERED"
        emoji = ":white_check_mark:"
    else:
        color = 15158332  # red
        status_text = "DOWN"
        emoji = ":red_circle:"

    # Persist the incident so the dashboard can show it (same content as Discord)
    try:
        async with AsyncSessionLocal() as db:
            await crud.create_incident(
                db,
                service=service,
                status=status_text,
                http_status_code=result["status_code"],
                response_time_ms=result["response_time_ms"],
                content_detail=result.get("content_detail"),
            )
    except Exception as exc:
        logger.error("incident_persist_failed", extra={"error": str(exc)})

    content_line = f"\n**Content check:** {result['content_detail']}" if result.get("content_detail") else ""
    payload = {
        "embeds": [
            {
                "title": f"{emoji} {service.name} is {status_text}",
                "description": (
                    f"**URL:** {service.url}\n"
                    f"**HTTP Status:** {result['status_code'] or 'No response'}\n"
                    f"**Latency:** {result['response_time_ms']} ms"
                    f"{content_line}"
                ),
                "color": color,
            }
        ]
    }

    try:
        client = get_http_client()
        resp = await client.post(settings.discord_webhook_url, json=payload)
        resp.raise_for_status()
    except Exception as exc:
        # Alert delivery failure must never crash the monitoring loop
        logger.error("discord_alert_failed", extra={"error": str(exc)})


async def run_monitoring_cycle() -> None:
    """Poll all monitored services, persist results, and fire alerts.

    This is the APScheduler job. A single async DB session is opened per
    cycle rather than per service to minimise connection churn.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(MonitoredService))
        services: list[MonitoredService] = result.scalars().all()

    if not services:
        logger.debug("no_services_to_check")
        return

    logger.info("monitoring_cycle_start", extra={"service_count": len(services)})

    for service in services:
        check_result = await check_service(service)

        async with AsyncSessionLocal() as db:
            check = HealthCheck(
                service_id=service.id,
                status_code=check_result["status_code"],
                response_time_ms=check_result["response_time_ms"],
                success=check_result["success"],
            )
            db.add(check)
            await db.commit()

        await maybe_alert_discord(service, check_result)

        logger.info(
            "check_complete",
            extra={
                "service_id": service.id,
                "url": service.url,
                "success": check_result["success"],
                "status_code": check_result["status_code"],
                "response_time_ms": check_result["response_time_ms"],
            },
        )

    logger.info("monitoring_cycle_end")
