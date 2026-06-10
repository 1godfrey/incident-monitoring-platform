import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.database import get_db
from app.schemas import ServiceCreate, ServiceResponse, ServiceUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/services", tags=["services"])


@router.get("/", response_model=list[ServiceResponse])
async def list_services(db: AsyncSession = Depends(get_db)):
    """Return all monitored services."""
    services = await crud.get_all_services(db)
    return services


@router.post("/", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def add_service(payload: ServiceCreate, db: AsyncSession = Depends(get_db)):
    """Register a new URL for monitoring.

    Returns 409 if the URL is already tracked — duplicate monitoring
    would skew uptime stats and spam Discord alerts.
    """
    try:
        service = await crud.create_service(db, payload)
        logger.info("service_created", extra={"service_id": service.id, "url": service.url})
        return service
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A service with this URL is already being monitored.",
        )


@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(service_id: int, payload: ServiceUpdate, db: AsyncSession = Depends(get_db)):
    """Update a monitored service's name, URL, or content-check configuration.

    Returns 409 if the new URL collides with another monitored service.
    """
    service = await crud.get_service(db, service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service {service_id} not found.",
        )

    try:
        updated = await crud.update_service(db, service, payload)
        logger.info("service_updated", extra={"service_id": service_id, "url": updated.url})
        return updated
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A service with this URL is already being monitored.",
        )


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_service(service_id: int, db: AsyncSession = Depends(get_db)):
    """Stop monitoring a service and delete its health check history."""
    service = await crud.get_service(db, service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service {service_id} not found.",
        )

    await crud.delete_service(db, service)
    logger.info("service_deleted", extra={"service_id": service_id})
