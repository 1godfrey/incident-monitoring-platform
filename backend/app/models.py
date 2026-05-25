from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MonitoredService(Base):
    __tablename__ = "monitored_services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True)
    # Optional content-based check: resolve json_path in the response body and
    # compare against expected_value. If they differ the check is marked failed
    # even when HTTP returns 2xx — useful for status-page APIs like GitHub's.
    json_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    expected_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    health_checks: Mapped[list["HealthCheck"]] = relationship(
        back_populates="service",
        cascade="all, delete-orphan",  # removing a service cleans up its history
    )


class HealthCheck(Base):
    __tablename__ = "health_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    service_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("monitored_services.id", ondelete="CASCADE"), index=True
    )
    # status_code is nullable: a network error produces no HTTP status
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    service: Mapped["MonitoredService"] = relationship(back_populates="health_checks")
