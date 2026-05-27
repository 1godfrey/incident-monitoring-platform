from datetime import datetime

from pydantic import BaseModel, HttpUrl, field_validator


# ── Service ──────────────────────────────────────────────────────────────────

class ServiceCreate(BaseModel):
    name: str
    url: HttpUrl  # validated at the API boundary; rejects malformed URLs
    # Optional content-based check configuration.
    # json_path: dot-notation path into the response JSON, e.g. "status.indicator"
    # expected_value: the value at that path that means healthy, e.g. "none"
    json_path: str | None = None
    expected_value: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be blank")
        return v.strip()


class ServiceResponse(BaseModel):
    id: int
    name: str
    url: str
    json_path: str | None
    expected_value: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Health Check ─────────────────────────────────────────────────────────────

class HealthCheckResponse(BaseModel):
    id: int
    service_id: int
    status_code: int | None
    response_time_ms: float
    success: bool
    checked_at: datetime

    model_config = {"from_attributes": True}


# ── Incident ──────────────────────────────────────────────────────────────────

class IncidentResponse(BaseModel):
    id: int
    service_id: int | None
    service_name: str
    service_url: str
    status: str               # "DOWN" | "RECOVERED"
    http_status_code: int | None
    response_time_ms: float
    content_detail: str | None
    triggered_at: datetime

    model_config = {"from_attributes": True}


# ── Summary ───────────────────────────────────────────────────────────────────

class ServiceSummary(BaseModel):
    service_id: int
    service_name: str
    service_url: str
    uptime_percentage: float       # over the last 24 hours
    avg_response_time_ms: float    # over the last 24 hours
    total_checks: int
    last_checked_at: datetime | None


class SummaryResponse(BaseModel):
    services: list[ServiceSummary]
