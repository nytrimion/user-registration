# Dependency Injection Strategy

Technical documentation for dependency injection architecture in the User Registration API.

## Table of Contents

- [Overview](#overview)
- [Technology Choice: injector](#technology-choice-injector)
- [Architecture Principles](#architecture-principles)
- [Implementation Guide](#implementation-guide)
- [Testing Strategy](#testing-strategy)
- [Examples](#examples)
- [Migration Path](#migration-path)

---

## Overview

This project uses **`injector`** + **`fastapi-injector`** for dependency injection across all architectural layers.

### Why Dependency Injection?

Dependency Injection (DI) is a design pattern that implements **Inversion of Control (IoC)** for resolving dependencies. Instead of components creating their own dependencies, they receive them from an external source.

**Benefits:**
- ✅ **Testability**: Easy to mock dependencies in unit tests
- ✅ **Maintainability**: Change implementations without modifying consumers
- ✅ **Decoupling**: Components depend on interfaces, not concrete implementations
- ✅ **Clean Architecture**: Application layer independent of infrastructure details

---

## Technology Choice: `injector`

### Comparison of DI Solutions

| Feature | FastAPI `Depends()` | `injector` | `dependency-injector` |
|---------|---------------------|------------|----------------------|
| **HTTP request scope** | ✅ Native support | ✅ Via `fastapi-injector` | ✅ Via `Provide[Container.X]` |
| **Non-HTTP contexts** | ❌ Limited to HTTP cycle | ✅ Works everywhere | ✅ Works everywhere |
| **Event handlers** | ❌ Cannot inject | ✅ Full support | ✅ Full support |
| **CLI/Jobs** | ❌ Requires workarounds | ✅ Framework-agnostic | ✅ Framework-agnostic |
| **DDD multi-layer** | ⚠️ Difficult in domain | ✅ Seamless | ✅ Seamless |
| **Configuration** | ✅ Zero setup | ⚠️ Minimal setup | ⚠️ Container boilerplate |
| **Testing** | ⚠️ Needs `dependency_overrides` | ✅ Direct injection | ✅ Container overrides |
| **Documentation** | ✅ Excellent (FastAPI) | ⚠️ Good | ✅ Excellent |
| **Popularity** | ✅ Built-in FastAPI | ⚠️ Moderate | ✅ High |

### Decision: `injector` + `fastapi-injector`

**Rationale:**

1. **Event-Driven Architecture Requirement**
   - `AccountCreatedHandler` executes **asynchronously outside HTTP context**
   - Must inject `ActivationCodeRepository` + `EmailService` without FastAPI
   - `Depends()` cannot inject dependencies in background tasks or event handlers

2. **Clean Architecture Compliance**
   - Application layer must remain framework-agnostic
   - Handlers should not depend on FastAPI lifecycle
   - `injector` works seamlessly across domain/application/infrastructure layers

3. **Future Extensibility**
   - CLI commands (e.g., cleanup expired codes)
   - Scheduled jobs (e.g., send reminder emails)
   - Other frameworks or delivery mechanisms

4. **Testability**
   - Unit tests for handlers without `TestClient`
   - Direct dependency injection in tests (no `app.dependency_overrides`)
   - Simpler mocking with explicit constructor injection

**Trade-offs Accepted:**
- ⚠️ External dependency (`injector` + `fastapi-injector`)
- ⚠️ `@inject` decorator required on constructors
- ⚠️ Slight learning curve for Python beginners

**Reference:** [SFEIR - Dependency Injection in Python](https://www.sfeir.dev/back/di-en-python/)

---

## Architecture Principles

### 1. Dependency Flow (Clean Architecture)

```
┌─────────────────────────────────────────────────────────────┐
│                      Infrastructure Layer                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Dependency Injection Module                  │  │
│  │  (binds interfaces → concrete implementations)       │  │
│  └──────────────────────────────────────────────────────┘  │
│         ▲                                       ▲            │
│         │ provides                              │ provides   │
│         │                                       │            │
│  ┌──────┴───────┐                        ┌─────┴─────────┐  │
│  │ FastAPI      │                        │ Event         │  │
│  │ Controllers  │                        │ Dispatcher    │  │
│  └──────────────┘                        └───────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │                                       │
         │ injects                               │ injects
         ▼                                       ▼
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
│  ┌────────────────────┐           ┌──────────────────────┐  │
│  │ CQRS Handlers      │           │ Event Handlers       │  │
│  │ (Commands/Queries) │           │ (Domain Events)      │  │
│  └────────────────────┘           └──────────────────────┘  │
│         │                                   │                │
│         │ depends on                        │ depends on     │
│         ▼                                   ▼                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Repository Interfaces (ABC)                  │  │
│  │         Service Interfaces (ABC)                     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         ▲
         │ implements
         │
┌─────────────────────────────────────────────────────────────┐
│                       Domain Layer                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Entities, Value Objects, Domain Events              │  │
│  │  (Pure business logic - no dependencies)             │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Key Principle:** Dependencies point **inward** (infrastructure → application → domain).

### 2. CQRS File Organization: Simplified Approach

This project uses a **pragmatic CQRS structure** suitable for small-to-medium projects (< 10 use cases).

#### Command + Handler: Merged in Single File ✨

For **CQRS command handlers**, we merge the Command (DTO) and Handler (business logic) in the **same file**:

```python
# ✅ RECOMMENDED: application/commands/register_account.py
@dataclass(frozen=True)
class RegisterAccountCommand:
    """Immutable command DTO."""
    email: Email
    password: Password

class RegisterAccountHandler:
    """Handler for RegisterAccountCommand."""
    @inject
    def __init__(self, repository: AccountRepository):
        self._repository = repository

    def handle(self, command: RegisterAccountCommand) -> None:
        # Business logic
        pass
```

**Rationale**:
- ✅ **Cohesion**: Command and Handler are logically coupled (always used together)
- ✅ **Simplicity**: 1 file vs 3 files (`__init__.py` + `command.py` + `handler.py`)
- ✅ **Reduced boilerplate**: No need for separate modules for small use cases
- ✅ **Clear imports**: `from ...commands.register_account import RegisterAccountCommand, RegisterAccountHandler`

**When to separate**:
- ❌ **Avoid separation** for projects < 10 use cases (over-engineering)
- ✅ **Consider separation** for projects > 20 use cases (easier navigation)

#### Event Handlers: Separate Files ⚠️

**Event handlers remain in separate files** because:

1. **Different dependencies**: Event handlers have different dependencies than command handlers
   ```python
   # Command handler needs: AccountRepository
   # Event handler needs: ActivationCodeRepository + EmailService
   ```

2. **Different execution context**: Event handlers run **asynchronously outside HTTP cycle**
   ```python
   # Command: HTTP request → synchronous
   # Event: Background task → asynchronous
   ```

3. **Different testing strategy**: Event handlers test async workflows, command handlers test business rules

**Structure**:
```python
# ✅ CORRECT: Separate file for event handlers
# application/events/account_created_handler.py
class AccountCreatedHandler:
    @inject
    def __init__(
        self,
        activation_code_repository: ActivationCodeRepository,
        email_service: EmailService,
    ):
        pass
```

#### Comparison: Separated vs Merged

| Approach | Files | Imports | Complexity | Best For |
|----------|-------|---------|------------|----------|
| **Merged Command+Handler** | 1 file | `from .register_account import ...` | Low | < 10 use cases |
| **Separated Command+Handler** | 3 files | `from .register_account.handler import ...` | High | > 20 use cases |
| **Event Handler (always separate)** | 1 file per event | `from .events.account_created_handler import ...` | Medium | All projects |

#### Example Structure for This Project

```
application/
├── commands/
│   ├── register_account.py       # ✨ Command + Handler (merged)
│   └── activate_account.py       # ✨ Command + Handler (merged)
├── events/
│   └── account_created_handler.py  # ⚠️ Event handler (separate)
└── contracts/
    └── services/
        └── email_service.py
```

**Key takeaway**: **Simplify where possible** (Command+Handler merged), but **separate when necessary** (Event handlers).

### 3. Injection Scopes

| Scope | Lifecycle | Use Case | Example |
|-------|-----------|----------|---------|
| **Singleton** | One instance per application | Stateful services, connection pools | `PostgresAccountRepository` (reuses DB pool) |
| **Request** | One instance per HTTP request | Request-scoped data | (Not used - see note below) |
| **Transient** | New instance per injection | Stateless components | `RegisterAccountHandler` |

**Note on Request Scope:**
- `injector` doesn't have built-in request scope like `dependency-injector`
- `fastapi-injector` handles request-scoped dependencies via FastAPI's native mechanism
- Handlers are **transient** (new instance per use case execution)
- Repositories are **singleton** (shared connection pool)

### 4. Interface-Based Design

All dependencies are injected via **abstract interfaces** (Python `ABC`):

```python
# ✅ GOOD: Depend on abstraction
class RegisterAccountHandler:
    @inject
    def __init__(self, repository: AccountRepository):  # ABC interface
        self._repository = repository

# ❌ BAD: Depend on concrete implementation
class RegisterAccountHandler:
    @inject
    def __init__(self, repository: PostgresAccountRepository):  # Concrete class
        self._repository = repository
```

**Benefits:**
- Application layer doesn't know about PostgreSQL
- Easy to swap implementations (e.g., PostgreSQL → MongoDB)
- Testable with mocks (mock the interface, not the implementation)

---

## Implementation Guide

### Step 1: Define Domain Interfaces

Interfaces belong to the **domain layer** (or **application/contracts** for cross-layer services).

```python
# src/account/domain/repositories/account_repository.py
from abc import ABC, abstractmethod
from typing import Optional
from src.account.domain.entities.account import Account
from src.account.domain.value_objects.email import Email

class AccountRepository(ABC):
    """Repository interface for Account aggregate."""

    @abstractmethod
    def create(self, account: Account) -> None:
        """Persist a new account."""
        pass

    @abstractmethod
    def find_by_email(self, email: Email) -> Optional[Account]:
        """Find account by email address."""
        pass
```

### Step 2: Implement Infrastructure Layer

Concrete implementations reside in **infrastructure layer**.

```python
# src/account/infrastructure/persistence/postgres_account_repository.py
from typing import Optional
from src.account.domain.repositories.account_repository import AccountRepository
from src.account.domain.entities.account import Account
from src.account.domain.value_objects.email import Email

class PostgresAccountRepository(AccountRepository):
    """PostgreSQL implementation of AccountRepository."""

    def __init__(self, connection_pool):
        """
        Initialize repository with database connection pool.

        Args:
            connection_pool: PostgreSQL connection pool (singleton)
        """
        self._pool = connection_pool

    def create(self, account: Account) -> None:
        """Persist account in PostgreSQL."""
        # SQL implementation...
        pass

    def find_by_email(self, email: Email) -> Optional[Account]:
        """Find account by email in PostgreSQL."""
        # SQL implementation...
        pass
```

### Step 3: Create Injection Module

Centralized binding configuration in **infrastructure layer**.

```python
# src/shared/infrastructure/di/injection_module.py
from injector import Binder, Module, singleton

from src.account.domain.repositories.account_repository import AccountRepository
from src.account.infrastructure.persistence.postgres_account_repository import (
    PostgresAccountRepository,
)
from src.account.application.commands.register_account import RegisterAccountHandler

class ApplicationModule(Module):
    """
    Injector module defining all application bindings.

    This module is the single source of truth for dependency configuration.
    All interface → implementation mappings are defined here.
    """

    def configure(self, binder: Binder) -> None:
        """
        Bind interfaces to implementations.

        Args:
            binder: Injector binder for dependency registration
        """
        # === REPOSITORIES (Singletons) ===
        # Singleton scope: One instance shared across application
        # Reuses database connection pool for performance
        binder.bind(
            AccountRepository,
            to=PostgresAccountRepository,
            scope=singleton,
        )

        # === HANDLERS (Transient - default scope) ===
        # New instance per injection (stateless handlers)
        # injector auto-wires constructor dependencies
        binder.bind(RegisterAccountHandler, to=RegisterAccountHandler)

        # === SERVICES (Singletons) ===
        # Email service, cache, external APIs, etc.
        # binder.bind(EmailService, to=ConsoleEmailService, scope=singleton)
```

**Design Decisions:**

1. **Explicit bindings** - All dependencies registered in one place
2. **Scope annotations** - Clear lifecycle management (`singleton` vs transient)
3. **Auto-wiring** - `injector` resolves constructor dependencies automatically

### Step 4: Integrate with FastAPI

Attach `injector` to FastAPI application in `main.py`.

```python
# main.py
from fastapi import FastAPI
from fastapi_injector import attach_injector
from injector import Injector

from src.shared.infrastructure.di.injection_module import ApplicationModule
from src.account.infrastructure.http.account_controller import router as account_router

# Create injector with application module
injector = Injector([ApplicationModule()])

# Create FastAPI app
app = FastAPI(
    title="User Registration API",
    version="1.0.0",
)

# Attach injector to FastAPI
# This enables @inject decorator in route handlers
attach_injector(app, injector)

# Register routers
app.include_router(account_router)
```

**What `attach_injector()` does:**
- Wraps FastAPI routes to resolve `@inject` dependencies
- Manages dependency lifecycle per request
- Integrates `injector` with FastAPI's request/response cycle

### Step 5: Inject into Application Handlers

Use `@inject` decorator on handler constructors.

```python
# src/account/application/commands/register_account.py
"""
Register account use case.

Command and handler merged in single file (pragmatic CQRS for < 10 use cases).
"""
from dataclasses import dataclass
from injector import inject

from src.account.domain.repositories.account_repository import AccountRepository
from src.account.domain.entities.account import Account
from src.account.domain.value_objects.email import Email
from src.account.domain.value_objects.password import Password
from src.account.domain.exceptions import EmailAlreadyExistsError


@dataclass(frozen=True)
class RegisterAccountCommand:
    """
    Command to register a new account.

    Immutable DTO carrying registration data from presentation layer
    to application layer.
    """
    email: Email
    password: Password


class RegisterAccountHandler:
    """
    CQRS command handler for account registration.

    This handler is framework-agnostic - it doesn't depend on FastAPI.
    Dependencies are injected via @inject decorator.
    """

    @inject
    def __init__(self, repository: AccountRepository):
        """
        Initialize handler with injected dependencies.

        Args:
            repository: Account repository (injected by injector)
        """
        self._repository = repository

    def handle(self, command: RegisterAccountCommand) -> None:
        """
        Execute account registration use case.

        Business rules enforced:
        - Email uniqueness across all accounts
        - Password is already hashed (validated by Password VO)

        Args:
            command: Registration command with validated data

        Raises:
            EmailAlreadyExistsError: If email already registered
        """
        # Business rule: Email must be unique
        existing_account = self._repository.find_by_email(command.email)
        if existing_account is not None:
            raise EmailAlreadyExistsError(command.email)

        # Create and persist account
        account = Account.create(command.email, command.password)
        self._repository.create(account)
```

**Key Points:**
- ✅ `@inject` decorator on `__init__`
- ✅ Type hints enable auto-wiring (`repository: AccountRepository`)
- ✅ No FastAPI imports - handler is framework-agnostic
- ✅ Testable without FastAPI (see testing section)

### Step 6: Inject into FastAPI Controllers

Use `@inject` decorator on route handlers.

```python
# src/account/infrastructure/http/account_controller.py
from fastapi import APIRouter, HTTPException, status
from injector import inject
from pydantic import BaseModel, EmailStr, Field

from src.account.application.commands.register_account import (
    RegisterAccountCommand,
    RegisterAccountHandler,
)
from src.account.domain.value_objects.email import Email
from src.account.domain.value_objects.password import Password
from src.account.domain.exceptions import EmailAlreadyExistsError

router = APIRouter(prefix="/accounts", tags=["accounts"])

class RegisterAccountRequest(BaseModel):
    """HTTP DTO for account registration."""
    email: EmailStr
    password: str = Field(min_length=8)

@router.post("", status_code=status.HTTP_201_CREATED)
@inject
async def register_account(
    request: RegisterAccountRequest,
    handler: RegisterAccountHandler,  # Injected by fastapi-injector
) -> None:
    """
    Register a new user account.

    Args:
        request: Registration data (HTTP DTO)
        handler: Use case handler (injected)

    Raises:
        409 Conflict: Email already registered
        400 Bad Request: Invalid email/password format
    """
    try:
        command = RegisterAccountCommand(
            email=Email(request.email),
            password=Password.from_plain_text(request.password),
        )
        handler.handle(command)
    except EmailAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email {e.email.value} is already registered",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
```

**Important Notes:**
- ✅ `@inject` decorator required on route handler
- ✅ No `Depends()` needed - `fastapi-injector` handles injection
- ✅ Handler parameter type-hinted (`handler: RegisterAccountHandler`)
- ✅ HTTP → Domain conversion (`RegisterAccountRequest` → `RegisterAccountCommand`)

### Step 7: Inject into Event Handlers (Non-HTTP Context)

Event handlers run **outside HTTP request cycle** - this is where `injector` shines.

```python
# src/account/application/events/account_created_handler.py
from injector import inject

from src.account.domain.events.account_created import AccountCreated
from src.account.domain.repositories.activation_code_repository import (
    ActivationCodeRepository,
)
from src.account.application.contracts.services.email_service import EmailService
from src.account.domain.value_objects.activation_code import ActivationCode

class AccountCreatedHandler:
    """
    Domain event handler for AccountCreated event.

    This handler executes ASYNCHRONOUSLY in a background task,
    OUTSIDE the HTTP request/response cycle.

    With injector, dependencies are resolved WITHOUT FastAPI.
    """

    @inject
    def __init__(
        self,
        activation_code_repository: ActivationCodeRepository,
        email_service: EmailService,
    ):
        """
        Initialize handler with injected dependencies.

        Args:
            activation_code_repository: Repository for activation codes (injected)
            email_service: Email service for sending codes (injected)
        """
        self._activation_code_repository = activation_code_repository
        self._email_service = email_service

    def handle(self, event: AccountCreated) -> None:
        """
        Handle account creation event.

        Generates activation code and sends email asynchronously.

        Args:
            event: AccountCreated domain event
        """
        # Generate 4-digit code with 60-second expiration
        code = ActivationCode.generate(expires_in_seconds=60)

        # Persist code
        self._activation_code_repository.save(event.account_id, code)

        # Send email (async - no HTTP context)
        self._email_service.send_activation_code(event.email, code)
```

**Event Dispatcher (Non-HTTP Context):**

```python
# src/shared/infrastructure/events/event_dispatcher.py
from injector import Injector

class EventDispatcher:
    """
    Simple synchronous event dispatcher.

    Uses injector to resolve event handlers outside HTTP context.
    """

    def __init__(self, injector: Injector):
        """
        Initialize dispatcher with injector.

        Args:
            injector: Injector instance for resolving handlers
        """
        self._injector = injector
        self._handlers: dict[type, type] = {}

    def register(self, event_type: type, handler_type: type) -> None:
        """
        Register event handler.

        Args:
            event_type: Domain event class
            handler_type: Handler class (will be resolved via injector)
        """
        self._handlers[event_type] = handler_type

    def dispatch(self, event: object) -> None:
        """
        Dispatch event to registered handler.

        Args:
            event: Domain event instance
        """
        handler_type = self._handlers.get(type(event))
        if handler_type:
            # injector resolves handler with dependencies
            handler = self._injector.get(handler_type)
            handler.handle(event)

# Usage in main.py
from src.account.domain.events.account_created import AccountCreated
from src.account.application.events.account_created_handler import AccountCreatedHandler

dispatcher = EventDispatcher(injector)
dispatcher.register(AccountCreated, AccountCreatedHandler)

# In RegisterAccountHandler (after repository.create)
dispatcher.dispatch(AccountCreated(account.id, account.email))
```

**Critical Advantage:**
- ✅ `AccountCreatedHandler` injected **without FastAPI `Depends()`**
- ✅ Works in background tasks, CLI scripts, scheduled jobs
- ✅ Same DI mechanism across all contexts (HTTP + non-HTTP)

---

## Testing Strategy

### Unit Tests: Direct Injection (No `injector`)

For **unit tests**, inject mocks **directly** without `injector` for simplicity.

```python
# tests/unit/account/application/commands/test_register_account.py
from unittest.mock import Mock
import pytest

from src.account.application.commands.register_account import (
    RegisterAccountCommand,
    RegisterAccountHandler,
)
from src.account.domain.repositories.account_repository import AccountRepository
from src.account.domain.exceptions import EmailAlreadyExistsError
from src.account.domain.value_objects.email import Email
from src.account.domain.value_objects.password import Password

def test_register_account_creates_new_account():
    """Test successful account registration."""
    # Arrange: Create mock repository
    mock_repository = Mock(spec=AccountRepository)
    mock_repository.find_by_email.return_value = None

    # Direct injection (no injector needed)
    handler = RegisterAccountHandler(mock_repository)

    email = Email("user@example.com")
    password = Password.from_plain_text("SecurePass123")
    command = RegisterAccountCommand(email, password)

    # Act
    handler.handle(command)

    # Assert
    mock_repository.find_by_email.assert_called_once_with(email)
    mock_repository.create.assert_called_once()

    # Verify created account properties
    created_account = mock_repository.create.call_args[0][0]
    assert created_account.email == email
    assert created_account.password == password
    assert created_account.is_activated is False

def test_register_account_raises_error_if_email_exists():
    """Test email uniqueness validation."""
    # Arrange
    existing_account = Mock()
    mock_repository = Mock(spec=AccountRepository)
    mock_repository.find_by_email.return_value = existing_account

    handler = RegisterAccountHandler(mock_repository)

    email = Email("existing@example.com")
    command = RegisterAccountCommand(email, Password.from_plain_text("Pass123"))

    # Act & Assert
    with pytest.raises(EmailAlreadyExistsError) as exc_info:
        handler.handle(command)

    assert exc_info.value.email == email
    mock_repository.create.assert_not_called()
```

**Advantages:**
- ✅ No `injector` setup needed in tests
- ✅ Explicit mock creation (clear test intent)
- ✅ Fast test execution (no DI overhead)
- ✅ Simple debugging (no hidden injection magic)

### Unit Tests: With `injector` (Optional)

For **integration-like unit tests**, use `injector` with test bindings.

```python
# tests/unit/account/application/commands/test_register_account_with_injector.py
from unittest.mock import Mock
from injector import Injector, Binder

from src.account.application.commands.register_account import RegisterAccountHandler
from src.account.domain.repositories.account_repository import AccountRepository

def test_register_account_with_injector():
    """Test handler with injector (demonstrates DI in tests)."""
    # Arrange: Create test injector with mock repository
    mock_repository = Mock(spec=AccountRepository)
    mock_repository.find_by_email.return_value = None

    def configure_test_binder(binder: Binder) -> None:
        binder.bind(AccountRepository, to=mock_repository)

    test_injector = Injector([configure_test_binder])

    # Act: Resolve handler via injector
    handler = test_injector.get(RegisterAccountHandler)

    # Handler now has mock_repository injected
    assert handler._repository is mock_repository
```

**Use Case:**
- Testing DI configuration itself
- Validating module bindings
- Integration-like tests without real infrastructure

### Integration Tests: With FastAPI TestClient

For **integration tests**, use `TestClient` with dependency overrides.

```python
# tests/integration/account/http/test_account_endpoints.py
from fastapi.testclient import TestClient
from unittest.mock import Mock

from main import app
from src.account.domain.repositories.account_repository import AccountRepository
from src.account.application.commands.register_account.register_account_handler import (
    RegisterAccountHandler,
)

def test_register_account_endpoint_success():
    """Test POST /accounts endpoint with mocked repository."""
    # Arrange: Create mock repository
    mock_repository = Mock(spec=AccountRepository)
    mock_repository.find_by_email.return_value = None

    # Override injector binding for test
    # (requires access to injector instance from main.py)
    from main import injector
    from injector import Binder

    def override_binder(binder: Binder) -> None:
        binder.bind(AccountRepository, to=mock_repository)

    # Create test client with overridden injector
    # NOTE: This requires exposing injector in main.py for tests
    test_injector = Injector([override_binder])
    # ... (integration test setup depends on project structure)

    client = TestClient(app)

    # Act
    response = client.post(
        "/accounts",
        json={"email": "user@example.com", "password": "SecurePass123"},
    )

    # Assert
    assert response.status_code == 201
    mock_repository.create.assert_called_once()
```

**Note:** Integration testing with `injector` requires careful setup. Consider using:
- Environment-specific injector modules (test vs production)
- Dependency override mechanisms (similar to FastAPI's `app.dependency_overrides`)

---

## Examples

### Example 1: HTTP Context (FastAPI Route)

```python
# Flow: HTTP Request → FastAPI → Handler (with injected repository)

# 1. User sends POST /accounts
POST http://localhost:8000/accounts
{
  "email": "user@example.com",
  "password": "SecurePass123"
}

# 2. FastAPI route handler (with @inject)
@router.post("", status_code=201)
@inject
async def register_account(
    request: RegisterAccountRequest,
    handler: RegisterAccountHandler,  # ← Injected by fastapi-injector
):
    handler.handle(...)

# 3. injector resolves RegisterAccountHandler
# - Sees constructor: __init__(self, repository: AccountRepository)
# - Looks up AccountRepository in ApplicationModule
# - Finds binding: AccountRepository → PostgresAccountRepository (singleton)
# - Returns existing PostgresAccountRepository instance
# - Instantiates RegisterAccountHandler(postgres_repository)

# 4. Handler executes business logic with injected repository
handler.handle(command)  # Uses self._repository (PostgreSQL)
```

### Example 2: Non-HTTP Context (Event Handler)

```python
# Flow: Domain Event → Event Dispatcher → Handler (with injected dependencies)

# 1. Account created, event emitted
account = Account.create(email, password)
repository.create(account)
event = AccountCreated(account.id, account.email)
dispatcher.dispatch(event)

# 2. Event dispatcher resolves handler via injector
handler_type = self._handlers[AccountCreated]  # → AccountCreatedHandler
handler = self._injector.get(handler_type)  # ← Injector resolves dependencies

# 3. injector resolves AccountCreatedHandler
# - Constructor: __init__(self, activation_code_repo, email_service)
# - Looks up ActivationCodeRepository → PostgresActivationCodeRepository (singleton)
# - Looks up EmailService → ConsoleEmailService (singleton)
# - Instantiates AccountCreatedHandler(postgres_repo, console_service)

# 4. Handler executes (outside HTTP context)
handler.handle(event)  # Generates code, sends email
```

### Example 3: CLI Script (Future Use Case)

```python
# src/cli/cleanup_expired_codes.py
"""CLI script to cleanup expired activation codes."""
from injector import Injector
from src.shared.infrastructure.di.injection_module import ApplicationModule
from src.account.domain.repositories.activation_code_repository import (
    ActivationCodeRepository,
)

def main():
    # Create injector (same configuration as FastAPI)
    injector = Injector([ApplicationModule()])

    # Resolve repository (singleton instance with connection pool)
    repository = injector.get(ActivationCodeRepository)

    # Business logic
    deleted_count = repository.delete_expired()
    print(f"Deleted {deleted_count} expired codes")

if __name__ == "__main__":
    main()
```

**Key Point:** Same `injector` configuration works in **CLI, FastAPI, event handlers, tests** - true framework-agnostic DI.

---

## Migration Path

### Current State (After This PR)

- ✅ `injector` + `fastapi-injector` installed
- ✅ `ApplicationModule` defined with bindings
- ✅ `RegisterAccountHandler` using `@inject`
- ✅ FastAPI integration via `attach_injector()`

### Future Enhancements

#### 1. Configuration Management

Currently, repositories are hardcoded. Future improvement:

```python
# ApplicationModule with configuration
class ApplicationModule(Module):
    def __init__(self, config: dict):
        self.config = config

    def configure(self, binder: Binder) -> None:
        # Use config values
        binder.bind(
            AccountRepository,
            to=PostgresAccountRepository(
                connection_string=self.config["database_url"]
            ),
            scope=singleton,
        )

# In main.py
from config import load_config
config = load_config()  # From env vars, .env file, etc.
injector = Injector([ApplicationModule(config)])
```

#### 2. Environment-Specific Modules

Separate modules for development/testing/production:

```python
# src/shared/infrastructure/di/test_module.py
class TestModule(Module):
    """Test-specific bindings (in-memory repositories, mocked services)."""

    def configure(self, binder: Binder) -> None:
        binder.bind(AccountRepository, to=InMemoryAccountRepository, scope=singleton)
        binder.bind(EmailService, to=MockEmailService, scope=singleton)

# In tests
test_injector = Injector([TestModule()])
```

#### 3. Lazy Initialization

For expensive resources (DB connections), use `injector` providers:

```python
from injector import provider

class ApplicationModule(Module):
    @provider
    @singleton
    def provide_account_repository(self) -> AccountRepository:
        # Lazy initialization of connection pool
        pool = create_connection_pool(...)  # Only created when first needed
        return PostgresAccountRepository(pool)
```

### Migration from `Depends()` (If Needed)

If starting with native FastAPI `Depends()` and migrating to `injector`:

1. Install `injector` + `fastapi-injector`
2. Create `ApplicationModule` with existing dependencies
3. Replace `Depends(get_repository)` with `@inject` decorator
4. Remove manual provider functions (e.g., `get_account_repository()`)
5. Update tests to use direct injection or test injector

**Estimated Effort:** ~2 hours for small projects (< 10 dependencies).

---

## References

### Documentation
- [injector on PyPI](https://pypi.org/project/injector/)
- [injector GitHub Repository](https://github.com/python-injector/injector)
- [fastapi-injector GitHub Repository](https://github.com/maldoinc/fastapi-injector)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)

### Articles
- [SFEIR - Dependency Injection in Python](https://www.sfeir.dev/back/di-en-python/) (French)
- [Dependency Injection in Python Beyond FastAPI's Depends](https://medium.com/@guillaume.launay/dependency-injection-in-python-beyond-fastapis-depends-eec237b1327b)
- [Better Dependency Injection in FastAPI](https://vladiliescu.net/better-dependency-injection-in-fastapi/)

### Related Patterns
- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Domain-Driven Design by Eric Evans](https://www.domainlanguage.com/ddd/)
- [CQRS Pattern](https://martinfowler.com/bliki/CQRS.html)

---

## FAQ

### Q: Why not use `dependency-injector` instead?

**A:** While `dependency-injector` has better documentation, it has two drawbacks:
1. **Container leakage** - Routes must know about the container (`Depends(Provide[Container.X])`)
2. **Irregular maintenance** - Development gap between Dec 2022 - Aug 2024

`injector` is simpler (`@inject` decorator only) and actively maintained.

### Q: Can I use `Depends()` for some dependencies and `@inject` for others?

**A:** Yes, but **not recommended**. Mixing DI mechanisms creates confusion:
- Which dependencies use `Depends()`?
- Which use `@inject`?
- How do they interact?

**Best practice:** Choose one mechanism project-wide.

### Q: Do I need `@inject` on every class?

**A:** Only on classes that:
1. Receive injected dependencies via constructor
2. Are instantiated by `injector` (not manually)

**Don't need `@inject`:**
- Value objects (immutable, no dependencies)
- Entities (created via factory methods)
- DTOs (data transfer objects)

### Q: How do I inject primitives (strings, ints)?

**A:** Use named bindings with `Key`:

```python
from injector import Key

DatabaseUrl = Key("database_url")

# In module
binder.bind(DatabaseUrl, to="postgresql://localhost/db")

# In class
@inject
def __init__(self, db_url: DatabaseUrl):
    self.db_url = db_url
```

### Q: What about async dependencies?

**A:** `injector` doesn't have built-in async support. For async initialization:

```python
class PostgresAccountRepository:
    def __init__(self):
        self._pool = None  # Initialized lazily

    async def _ensure_pool(self):
        if self._pool is None:
            self._pool = await create_async_pool()
```

Or use factory pattern with `@provider` and manual async setup in `main.py`.

---

## Conclusion

This project uses **`injector`** for dependency injection to achieve:

1. ✅ **Framework-agnostic architecture** - Application layer independent of FastAPI
2. ✅ **Event-driven design** - Inject dependencies in async event handlers
3. ✅ **Testability** - Easy mocking with interface-based design
4. ✅ **Clean Architecture** - Dependency inversion across all layers
5. ✅ **Future extensibility** - Same DI works in CLI, jobs, other frameworks

The `@inject` decorator and `ApplicationModule` provide a **simple, explicit, and scalable** DI solution suitable for production-grade Python applications.