"""Health check endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from services.health_service import HealthService
from config import get_settings


router = APIRouter(tags=["health"])


class HealthCheck(BaseModel):
    """Health check response model."""

    status: str
    version: str
    checks: dict


@router.get("/health")
async def health_check(
    health_service: HealthService = Depends(HealthService),
) -> HealthCheck:
    """Basic health check endpoint."""

    settings = get_settings()
    result = await health_service.check_basic_health()

    return HealthCheck(
        status="healthy" if result.healthy else "unhealthy",
        version=settings.version,
        checks=result.checks,
    )


@router.get("/health/detailed")
async def detailed_health_check(
    health_service: HealthService = Depends(HealthService),
) -> HealthCheck:
    """Detailed health check endpoint (same as basic for Landing API)."""

    settings = get_settings()
    result = await health_service.check_detailed_health()

    return HealthCheck(
        status="healthy" if result.healthy else "unhealthy",
        version=settings.version,
        checks=result.checks,
    )
