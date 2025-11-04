import logging
import os

from fastapi import FastAPI
from fastapi_injector import attach_injector
from injector import Injector

from src.account.application.events.account_created_handler import (
    AccountCreatedHandler,
)
from src.account.domain.events.account_created import AccountCreated
from src.account.infrastructure.di.account_module import AccountModule
from src.account.infrastructure.http.account_controller import (
    router as account_router,
)
from src.shared.domain.events.event_dispatcher import EventDispatcher
from src.shared.infrastructure.di.container import InfrastructureModule
from src.shared.infrastructure.http.health_controller import router as health_router

# Configure logging level from environment variable (default: INFO)
# Valid levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
# Set via LOG_LEVEL in .env or docker-compose.yml environment
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(levelname)s:%(name)s:%(message)s",
)
# Set application logger to configured level
logging.getLogger("src").setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

# Configure dependency injection
injector = Injector(
    [
        InfrastructureModule(),
        AccountModule(),
    ]
)

# Register event handlers
event_dispatcher = injector.get(EventDispatcher)  # type: ignore[type-abstract]
event_dispatcher.register(AccountCreated, AccountCreatedHandler)

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
