# User Registration API

Technical test implementation for account registration with email verification.

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Technical Stack](#technical-stack)
- [Domain Design](#domain-design)
- [API Endpoints](#api-endpoints)
- [Database Schema](#database-schema)
- [Getting Started](#getting-started)
- [Testing](#testing)
- [CI/CD Pipeline](#cicd-pipeline)
- [Development Workflow](#development-workflow)

## Overview

REST API for user registration with email-based account activation using a time-limited 4-digit verification code.

### Features
- User account creation with email and password
- Automatic verification code generation (4 digits)
- Email delivery of activation code
- Time-limited code validation (60 seconds)
- Account activation with Basic Authentication

## Architecture

### Clean Architecture & DDD

This project follows Clean Architecture principles with Domain-Driven Design tactical patterns.

<!-- Architecture diagram will be here -->
![Architecture Diagram](docs/architecture-diagram.png)

### Bounded Context: Account

The application is built around a single bounded context: **Account**.

#### Layer Structure

```
src/
├── account/                          # Bounded Context: Account
│   ├── domain/                       # Domain Layer (Business Logic)
│   │   ├── entities/
│   │   │   └── account.py           # Aggregate Root
│   │   ├── value_objects/
│   │   │   ├── email.py
│   │   │   ├── password.py
│   │   │   └── activation_code.py
│   │   ├── events/
│   │   │   └── account_created.py
│   │   ├── repositories/            # Repository Interfaces
│   │   │   ├── account_repository.py
│   │   │   └── activation_code_repository.py
│   │   └── exceptions/
│   │       └── domain_exceptions.py
│   ├── application/                  # Application Layer (Use Cases)
│   │   ├── contracts/               # External Service Interfaces
│   │   │   └── services/
│   │   │       └── email_service.py
│   │   ├── commands/                # CQRS Commands + Handlers
│   │   │   ├── register_account.py
│   │   │   └── activate_account.py
│   │   └── events/                  # Domain Event Handlers
│   │       └── account_created_handler.py
│   └── infrastructure/              # Infrastructure Layer (Technical Details)
│       ├── persistence/
│       │   ├── postgres_account_repository.py
│       │   └── postgres_activation_code_repository.py
│       ├── email/
│       │   └── console_email_service.py
│       └── http/
│           └── account_controller.py
└── main.py                          # FastAPI Application Entry Point
```

### Key Design Decisions

#### 1. Asynchronous Code Generation

**Flow:**
1. `POST /accounts` creates account (synchronous)
2. `AccountCreated` event emitted
3. Event handler generates code and sends email (asynchronous)

**Rationale:**
- Code generated just before email sending minimizes time window loss
- Handles message broker latency gracefully
- User gets maximum 60 seconds regardless of queue delays

**Benefits:**
- **Scalability**: Decouples account creation from email delivery (survives SMTP outages)
- **Resilience**: Account creation succeeds even if email service temporarily fails
- **User Experience**: Fast API response time (~50ms vs ~500ms with synchronous email)
- **Observability**: Separate metrics and monitoring for account creation vs email delivery

#### 2. DDD Encapsulation with @property

**Pattern:**
```python
# Entities are mutable but properties are encapsulated
account.activate()  # Only way to change is_activated
account.is_activated = True  # ❌ Raises AttributeError
repository.save(account)
```

**Rationale:**
- Properties protected via `@property` without setters
- Business rules enforced through domain methods only
- No Active Record anti-pattern (repository handles persistence)

**Benefits:**
- **Invariant Protection**: Impossible to bypass business rules (e.g., activate twice)
- **Explicitness**: Clear intent through method names (`activate()` vs property assignment)
- **Maintainability**: Business logic changes isolated to entity methods

#### 3. Separate Repository for Activation Codes

Two distinct repositories with clear responsibilities:
- **`AccountRepository`**: Manages account lifecycle (creation, retrieval, activation status)
- **`ActivationCodeRepository`**: Manages short-lived verification codes (creation, validation, deletion)

**Rationale:**
- Single Responsibility Principle compliance
- Independent testing with dedicated mocks
- Future evolution without coupling (e.g., code history, retry mechanisms)

**Benefits:**
- **Testability**: Mock each repository independently for faster, focused unit tests
- **Evolvability**: Switch activation code storage (Redis, in-memory cache) without touching Account logic
- **Performance**: Aggressive TTL/cleanup strategies for codes without impacting account data
- **Team Collaboration**: Multiple developers can work on each repository without merge conflicts

#### 4. Activation Code Primary Key: account_id (YAGNI Principle)

**Schema:**
```sql
CREATE TABLE account_activation_code (
  account_id UUID PRIMARY KEY,  -- Composite PK: account_id only
  code CHAR(4) NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  FOREIGN KEY (account_id) REFERENCES account(id) ON DELETE CASCADE
);
```

**Rationale:**
- YAGNI (You Aren't Gonna Need It): No code history required in current specs
- Primary key directly expresses business constraint: 1 active code per account
- Simpler than synthetic UUID + UNIQUE(account_id) constraint
- Easy migration path if historization needed later (duplicate account_id as new id column)

**Benefits:**
- **Simplicity**: No unnecessary UUID generation for temporary data
- **Explicitness**: Schema directly encodes "one code per account" rule
- **Performance**: Fewer indexes (no separate PK + UNIQUE constraint)
- **Maintainability**: Easy to evolve if requirements change (15-minute migration)

**Future-Proofing (if needed):**
```sql
-- Migration adds UUID while preserving data chronology
ALTER TABLE account_activation_code ADD COLUMN id UUID DEFAULT account_id;
-- UUID v7 from account preserves timestamp ordering
```

#### 5. Framework-Agnostic Dependency Injection

**Technology:** `injector` + `fastapi-injector` instead of FastAPI's native `Depends()`

**Flow:**
```python
# Handler is framework-agnostic (no FastAPI imports)
class RegisterAccountHandler:
    @inject
    def __init__(self, repository: AccountRepository):
        self._repository = repository

# FastAPI controller uses @inject decorator
@router.post("/accounts")
@inject
async def register(handler: RegisterAccountHandler):
    handler.handle(command)

# Event handler works outside HTTP context
class AccountCreatedHandler:
    @inject
    def __init__(self, code_repo: ActivationCodeRepository, email: EmailService):
        ...
```

**Rationale:**
- FastAPI's `Depends()` is **HTTP-request scoped only** - cannot inject dependencies in event handlers, CLI scripts, or background jobs
- Event-driven architecture requires DI outside the HTTP cycle (`AccountCreatedHandler` runs asynchronously)
- Clean Architecture compliance: Application layer must remain framework-agnostic

**Benefits:**
- **Event Handlers**: Inject repositories/services in async background tasks (impossible with `Depends()`)
- **Testability**: Unit test handlers with mocks without `TestClient` or `app.dependency_overrides`
- **Extensibility**: Same DI works in CLI commands, scheduled jobs, other frameworks
- **Clean Architecture**: Application handlers don't depend on FastAPI lifecycle

**Implementation:**
- `ApplicationModule` centralizes all bindings (interfaces → implementations)
- `@inject` decorator on handler constructors for auto-wiring
- Singleton repositories (connection pooling), transient handlers (stateless)

**Documentation:** See [`docs/dependency_injection.md`](docs/dependency_injection.md) for complete strategy and examples.

#### 6. No ORM - Raw SQL

Direct SQL queries using psycopg2 without Object-Relational Mapping.

**Rationale:**
- Explicit control over database operations
- Performance transparency (no hidden queries)
- No "magic" abstractions or auto-generated migrations
- Demonstrates raw SQL proficiency

**Benefits:**
- **Performance**: No N+1 queries, predictable execution plans, explicit JOINs
- **Debugging**: SQL logs directly usable in pgAdmin/psql for profiling
- **Control**: Fine-grained transaction management and locking strategies (SELECT FOR UPDATE)
- **Simplicity**: No migration auto-generation complexity

**Trade-offs Considered:**
- ❌ More boilerplate code (manual object mapping)
- ✅ But: Total visibility and control crucial for production debugging

## Technical Stack

### Core Technologies
- **Python**: 3.14
- **Dependency Management**: Poetry 1.8.4
- **Web Framework**: FastAPI (routing only)
- **Dependency Injection**: `injector` + `fastapi-injector` (framework-agnostic DI)
- **Database**: PostgreSQL 16
- **Database Driver**: psycopg2 (raw SQL, no ORM)
- **Database Migrations**: Yoyo-migrations (raw SQL migrations with rollback support)
- **Testing**: pytest, pytest-asyncio, pytest-cov, httpx
- **Code Quality**: black, ruff, mypy
- **Containerization**: Docker, Docker Compose

### Third-Party Services
- **Email Service**: Console output (production-ready abstraction for SMTP/HTTP API)

## Domain Design

### Aggregate Root
- **`Account`**: Core entity managing user registration and activation state

### Value Objects
- **`Email`**: Email address with validation
- **`Password`**: Hashed password with strength requirements
- **`ActivationCode`**: 4-digit code with expiration timestamp (60 seconds)

### Domain Events
- **`AccountCreated`**: Triggered after successful account persistence

### Repositories (Domain Interfaces)

#### AccountRepository
```python
def save(account: Account) -> None
def find_by_id(account_id: UUID) -> Optional[Account]
def find_by_email(email: Email) -> Optional[Account]
def mark_as_verified(account_id: UUID) -> None
```

#### ActivationCodeRepository
```python
def save(account_id: UUID, code: ActivationCode) -> None
def find_by_account_id(account_id: UUID) -> Optional[ActivationCode]
```

### Use Cases

#### RegisterAccount
- Creates account with email and password
- Persists account in database
- Emits `AccountCreated` event

#### ActivateAccount
- Validates Basic Auth credentials
- Verifies activation code and expiration
- Marks account as verified

## API Endpoints

### `POST /accounts`

Create a new user account and trigger verification email.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecureP@ssw0rd"
}
```

**Response:** `201 Created` No content

**Error Responses:**
- `400 Bad Request`: Invalid email format or weak password
- `409 Conflict`: Email already registered

---

### `POST /accounts/activate`

Activate account using 4-digit verification code.

**Authentication:** Basic Auth (email:password)

**Request:**
```json
{
  "code": "1234"
}
```

**Response:** `200 OK`
```json
{
  "message": "Account successfully activated"
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid credentials
- `400 Bad Request`: Invalid or expired code
- `404 Not Found`: No pending activation code

## Database Schema

### `account` table
```sql
CREATE TABLE account (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  is_verified BOOLEAN DEFAULT FALSE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW() NOT NULL
);
```

### `account_activation_code` table
```sql
CREATE TABLE account_activation_code (
  id UUID PRIMARY KEY,
  account_id UUID NOT NULL REFERENCES account(id) ON DELETE CASCADE,
  code CHAR(4) NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT NOW() NOT NULL,
  CONSTRAINT unique_active_code_per_account UNIQUE(account_id)
);
```

## Getting Started

### Prerequisites
- Docker
- Docker Compose

### Environment Configuration

The project uses environment variables for configuration. Default values are provided for development.

```bash
# (Optional) Copy environment template and customize
cp .env.example .env

# Edit .env if you want to change database credentials
# nano .env
```

**Note:** The application works out-of-the-box with default values. Creating `.env` is optional.

### Running the Application

```bash
# Start all services
docker-compose up -d

# Check application health
curl http://localhost:8000/health

# View logs
docker-compose logs -f api
```

The API will be available at `http://localhost:8000`.

### Database Migrations

The project uses **Yoyo-migrations** for database schema management with raw SQL migrations.

#### Migration Management

```bash
# Apply all pending migrations
docker-compose exec api python scripts/migrate.py

# Rollback last migration
docker-compose exec api python scripts/migrate.py --rollback

# List migration status
docker-compose exec api python scripts/migrate.py --list
```

#### Migration File Structure

Migrations follow a timestamp-based naming convention:

```
migrations/
├── 20251103_160000_create_account_table.sql          # Forward migration
└── 20251103_160000_create_account_table.rollback.sql # Rollback migration
```

**Key Points:**
- **Timestamp format**: `YYYYMMDD_HHMMSS_description.sql`
- **Separate rollback files**: `*.rollback.sql` for safe reversibility
- **Raw SQL**: No ORM magic, explicit schema definitions
- **Environment-aware**: Uses same DATABASE_* env vars as docker-compose.yml
- **CI/CD ready**: `scripts/migrate.py` wrapper for automated deployments

#### Creating New Migrations

```bash
# Manual creation with timestamp
touch migrations/$(date +%Y%m%d_%H%M%S)_add_user_roles.sql
touch migrations/$(date +%Y%m%d_%H%M%S)_add_user_roles.rollback.sql

# Edit the forward migration (*.sql)
# Add your CREATE TABLE / ALTER TABLE statements

# Edit the rollback migration (*.rollback.sql)
# Add corresponding DROP TABLE / ALTER TABLE statements
```

**Migration Best Practices:**
- ✅ Always test migrations on development database first
- ✅ Include both forward and rollback scripts
- ✅ Add comments explaining business rationale for schema changes
- ✅ Use IF NOT EXISTS / IF EXISTS for idempotency
- ⚠️ Avoid breaking changes in production (add columns as nullable first)

### Running Tests

```bash
# Run all tests
docker-compose run --rm api pytest

# Run unit tests only
docker-compose run --rm api pytest tests/unit

# Run integration tests only
docker-compose run --rm api pytest tests/integration

# Run with coverage
docker-compose run --rm api pytest --cov=src --cov-report=html
```

## Testing Strategy

### Coverage Goals
- **Target**: 90%+ coverage on business logic
- **Current**: 99% coverage (tracked via Codecov on CI)
- **Excluded**: `__repr__`, `if TYPE_CHECKING`, `if __name__ == "__main__"`

### Unit Tests
**Scope**: Domain entities, value objects, use cases (pure business logic)

**Mocking Strategy**:
- Repositories mocked with `unittest.mock` or `pytest-mock`
- External services (email) mocked to avoid I/O
- No database or HTTP dependencies

**Example**: `tests/unit/account/domain/entities/test_account.py` (19 tests, 100% coverage)
- Factory method validation
- Business rule enforcement (activate once)
- Entity identity pattern
- Encapsulation protection (AttributeError on direct property modification)

### Integration Tests
**Scope**: API endpoints, database operations, event handlers (full stack)

**Real Dependencies**:
- PostgreSQL test database (Docker service in CI)
- Full HTTP stack (FastAPI TestClient)
- Complete end-to-end flow validation

**Example**: `tests/integration/api/test_account_endpoints.py` (future)
- POST /accounts → 201 Created
- Email uniqueness constraint
- Activation flow with real database

### Test Structure
```
tests/
├── unit/
│   └── business_context
│       ├── domain/              # Value objects, entities
│       ├── application/         # Use cases with mocked repos
│       └── infrastructure/      # Mappers, validators
└── integration/
    └── business_context
        └── infrastructure/
            ├── http/            # HTTP endpoints
            └── repository/      # Database operations
```

## CI/CD Pipeline

### GitHub Actions

Automated quality checks run on every pull request and push to `main`:

**Workflow**: `.github/workflows/ci.yml` - 4 parallel jobs

1. **Lint** (`black` + `ruff`)
   - Code formatting validation (Black)
   - PEP 8 compliance and code quality (Ruff)
   - Import sorting and unused imports detection

2. **Type Check** (`mypy`)
   - Strict mode enabled (`strict = true`)
   - No `Any` types allowed
   - Full type coverage on business logic

3. **Test** (`pytest` + PostgreSQL service)
   - Unit tests (domain logic with mocks)
   - Integration tests (database, API)
   - Coverage report uploaded to Codecov
   - PostgreSQL 16 test database via Docker service

4. **Docker Build**
   - Validates `development` target
   - Validates `production` target
   - Ensures Docker images build successfully

**Status**: All jobs must pass before merging pull requests

### Pre-commit Hooks (Optional)

For faster feedback before pushing:

```bash
# Install pre-commit (if not using Docker)
pip install pre-commit

# Install hooks
pre-commit install

# Now black, ruff, mypy run automatically on git commit
```

**Note**: Not mandatory, CI will catch issues, but speeds up local development.

## Development Workflow

### Dependency Management

This project uses **Poetry** for dependency management (like Composer for PHP or npm for Node.js).

```bash
# Install dependencies inside container
docker-compose run --rm api poetry install

# Add a new dependency
docker-compose run --rm api poetry add <package>

# Add a dev dependency
docker-compose run --rm api poetry add --group dev <package>

# Update dependencies
docker-compose run --rm api poetry update
```

### Code Quality Tools

All tools are configured in `pyproject.toml`.

```bash
# Format code
docker-compose run --rm api poetry run black src tests

# Lint code
docker-compose run --rm api poetry run ruff check src tests

# Type checking
docker-compose run --rm api poetry run mypy src
```

### Contributing Workflow

This project follows **trunk-based development** with short-lived feature branches.

#### 1. Create Feature Branch

```bash
# Checkout main and pull latest
git checkout main
git pull origin main

# Create feature branch
git checkout -b feat/your-feature-name
```

#### 2. Development Cycle

```bash
# Make changes
# ...

# Run quality checks locally (recommended)
docker-compose run --rm api poetry run black src tests
docker-compose run --rm api poetry run ruff check src tests
docker-compose run --rm api poetry run mypy src
docker-compose run --rm api pytest

# Commit with conventional commits
git add .
git commit -m "feat: add account activation logic"
```

#### 3. Push and Create PR

```bash
# Push feature branch
git push origin feat/your-feature-name

# Create PR on GitHub
# CI will automatically run all quality checks
```

#### 4. Merge Strategy

- **Squash and merge** into `main`
- Delete feature branch after merge
- `main` is always deployable

### Conventional Commits

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` New feature
- `fix:` Bug fix
- `refactor:` Code refactoring (no functional change)
- `test:` Add or update tests
- `docs:` Documentation changes
- `chore:` Tooling, dependencies, config
- `ci:` CI/CD pipeline changes

**Example:**
```
feat: add account activation with time-limited codes

Implement ActivateAccount use case with:
- 4-digit code validation
- 60-second expiration check
- Basic Auth verification
```

## License

This is a technical test implementation for educational purposes.