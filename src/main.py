from fastapi import FastAPI

from src.shared.infrastructure.http.health_controller import router as health_router

app = FastAPI(
    title="User Registration API",
    description="REST API for user registration with email verification",
    version="0.1.0",
)

app.include_router(health_router)
