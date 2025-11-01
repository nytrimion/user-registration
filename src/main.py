from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(
    title="User Registration API",
    description="REST API for user registration with email verification",
    version="0.1.0",
)


@app.get("/health")
async def health_check() -> JSONResponse:
    """
    Health check endpoint for Docker and monitoring systems.
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )