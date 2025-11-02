from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class HealthCheckResponse(BaseModel):
    status: str = Field(
        ...,
        description="Health status of the service",
        examples=["ok"],
    )
    timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp of the health check",
        examples=["2025-11-02T14:27:05.107788+00:00"],
    )


@router.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """
    Health check endpoint for Docker and monitoring systems.

    Returns:
        HealthCheckResponse: Current service status and timestamp
    """
    return HealthCheckResponse(
        status="ok",
        timestamp=datetime.now(UTC).isoformat(),
    )
