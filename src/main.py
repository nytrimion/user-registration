from fastapi import FastAPI
from fastapi_injector import attach_injector
from injector import Injector

from src.account.infrastructure.di.account_module import AccountModule
from src.account.infrastructure.http.account_controller import (
    router as account_router,
)
from src.shared.infrastructure.di.container import InfrastructureModule
from src.shared.infrastructure.http.health_controller import router as health_router

# Configure dependency injection
injector = Injector(
    [
        InfrastructureModule(),
        AccountModule(),
    ]
)

app = FastAPI(
    title="User Registration API",
    description="REST API for user registration with email verification",
    version="0.1.0",
)

# Attach injector to FastAPI app for automatic dependency resolution
attach_injector(app, injector)

# Register routers
app.include_router(health_router)
app.include_router(account_router)
