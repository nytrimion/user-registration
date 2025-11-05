# User Registration API

Technical test of Python implementation for account registration with email verification.

## Table of Contents
- [Overview](#overview)
- [Getting Started](#getting-started)
- [Architecture](#architecture)
- [Technical Stack](#technical-stack)
- [Domain Design](#domain-design)
- [API Endpoints](#api-endpoints)
- [Database Schema](#database-schema)
- [Testing](#testing)
- [CI/CD Pipeline](#cicd-pipeline)
- [Development Workflow](#development-workflow)

## Overview

Python REST API for user registration with email-based account activation using a time-limited 4-digit verification code.

### Features
- User account creation with email and password
- Automatic verification code generation (4 digits)
- Email delivery of activation code
- Time-limited code validation (60 seconds)
- Account activation with Basic Authentication

## Getting Started

### Prerequisites
- Docker
- Docker Compose

### Environment Configuration

The project uses environment variables for configuration. Default values are provided for development.

```bash
# (Optional) Copy environment template and customize
cp .env.example .env

# Edit .env to customize configuration
# nano .env
```

**Key Environment Variables:**

**Database Configuration:**
- `DATABASE_HOST`: PostgreSQL host (default: `db`)
- `DATABASE_PORT`: PostgreSQL port (default: `5432`)
- `DATABASE_NAME`: Database name (default: `user_registration`)
- `DATABASE_USER`: Database username (default: `postgres`)
- `DATABASE_PASSWORD`: Database password (default: `postgres`)

**API Security:**
- `API_USERNAME`: Basic Auth username for activation endpoint (default: `api`)
- `API_PASSWORD`: Basic Auth password for activation endpoint (default: `secret`)

**Important:** Change `API_USERNAME` and `API_PASSWORD` in production environments to prevent unauthorized access to the activation endpoint.

**Note:** The application works out-of-the-box with default values. Creating `.env` is optional for local development.

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

## Architecture

### Clean Architecture & DDD

This project follows Clean Architecture principles with Domain-Driven Design tactical patterns.

<!-- Architecture diagram will be here -->
![Architecture Diagram](docs/architecture-diagram.png)

### Bounded Contexts

The application is built around a 2 bounded contexts:
- **account**: Account management
- **shared**: Application foundations & shared components

### Layer Structure

```
src/
├── account/                          # Bounded Context: Account
│   ├── domain/                       # Business Logic
│   │   ├── entities/                 # Account, AccountActivation
│   │   ├── value_objects/            # Email, Password, AccountId, ActivationCode
│   │   ├── repositories/             # Repository interfaces
│   │   ├── events/account_created.py # Domain events
│   │   └── exceptions.py             # Domain exceptions
│   ├── application/                  # Use Cases
│   │   ├── commands/                 # RegisterAccount, ActivateAccount (CQRS)
│   │   ├── events/                   # AccountCreatedHandler
│   │   └── contracts/services/       # EmailService interface
│   └── infrastructure/               # Technical Implementation
│       ├── persistence/              # PostgreSQL repositories + mappers
│       ├── http/                     # FastAPI controllers + DTOs
│       └── di/account_module.py      # DI bindings
├── shared/                           # Cross-Cutting Concerns
│   ├── domain/                       # Shared VOs (UuidV7), EventDispatcher interface
│   ├── application/                  # EmailService interface, EmailMessage DTO
│   └── infrastructure/
│       ├── database/connection.py    # Connection pool
│       ├── events/                   # InMemoryEventDispatcher
│       ├── http/auth.py              # Basic Auth utility
│       ├── services/                 # LoggerEmailService
│       └── di/container.py           # DI container setup
└── main.py                           # FastAPI app + event registration
```

### Key Design Decisions

This project implements several architectural patterns to ensure maintainability, scalability, and testability. 

For detailed analysis, trade-offs, and evolution paths, see [Architecture Decision Records (ADR)](docs/architecture-decisions.md).

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
- **Email Service**: Logger output (production-ready abstraction for SMTP/HTTP API)

## Domain Design

### Aggregate Root
- **`Account`**: Core entity managing user registration and activation state
- **`AccountActivation`**: Core entity managing activation code and its expiration date

### Value Objects
- **`AccountId`**: Account identifier as UUID version 7
- **`Email`**: Email address with validation
- **`Password`**: Hashed password with strength requirements
- **`ActivationCode`**: 4-digit code with expiration timestamp (60 seconds)

### Domain Events
- **`AccountCreated`**: Triggered after successful account persistence

### Repositories (Domain Interfaces)

#### AccountRepository
```python
def save(account: Account) -> None
def find_by_id(account_id: AccountId) -> Optional[Account]
def find_by_email(email: Email) -> Optional[Account]
```

#### AccountActivationRepository
```python
def save(activation: AccountActivation) -> None
def find_by_account_id(account_id: AccountId) -> Optional[AccountActivation]
```

**Note:** Uses UPSERT pattern (INSERT ... ON CONFLICT ... DO UPDATE) to enforce one code per account.

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

### `POST /accounts/{account_id}/activate`

Activate account using 4-digit verification code.

**Authentication:** Basic Auth (API credentials)
- Default username: `api`
- Default password: `secret`
- Configurable via environment variables: `API_USERNAME`, `API_PASSWORD`

**Path Parameters:**
- `account_id` (UUID): The account identifier to activate

**Request Body:**
```json
{
  "code": "1234"
}
```

**Response:** `200 OK` (no content)

**Example:**
```bash
# Using curl with default credentials
curl -X POST "http://localhost:8000/accounts/{account_id}/activate" \
  -u api:secret \
  -H "Content-Type: application/json" \
  -d '{"code": "1234"}'

# With custom credentials (if configured via env vars)
curl -X POST "http://localhost:8000/accounts/{account_id}/activate" \
  -u custom_user:custom_pass \
  -H "Content-Type: application/json" \
  -d '{"code": "1234"}'
```

**Error Responses:**
- `401 Unauthorized`: Invalid API credentials or missing Authorization header
- `400 Bad Request`: Invalid or expired activation code
- `404 Not Found`: Account or activation code not found
- `422 Unprocessable Entity`: Invalid UUID format or invalid code format (non-numeric)

## Database Schema

### `account` table
```sql
CREATE TABLE account (
  -- Primary Key: UUID v7 (time-ordered UUIDs for better index performance)
  id UUID PRIMARY KEY,
  -- Email: Business identifier, must be unique and normalized (lowercase)
  email VARCHAR(255) NOT NULL,
  -- Password: Bcrypt hash (60 characters for bcrypt, but allow extra space)
  password_hash VARCHAR(255) NOT NULL,
  -- Activation Status: Tracks whether account has been activated via code
  is_activated BOOLEAN NOT NULL DEFAULT FALSE,
  -- Audit: Creation timestamp (timezone-aware for global applications)
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  -- Audit: Last modification timestamp (updated explicitly by repository)
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  -- Business Rule: Email uniqueness constraint
  CONSTRAINT uq_account_email UNIQUE (email)
);
-- Performance Index: Accelerate find_by_email() queries
CREATE INDEX idx_account_email ON account(email);
```

### `account_activation` table
```sql
CREATE TABLE account_activation (
  -- Primary Key: account_id (enforces one code per account business rule)
  account_id UUID PRIMARY KEY,
  -- Activation Code: 4-digit numeric code (generated by ActivationCode VO)
  code VARCHAR(4) NOT NULL,
  -- Creation Timestamp: When activation was created (UTC)
  created_at TIMESTAMPTZ NOT NULL,
  -- Expiration Timestamp: When activation expires (created_at + 60 seconds)
  expires_at TIMESTAMPTZ NOT NULL,
  -- Foreign Key: Link to account table with CASCADE delete
  CONSTRAINT fk_account_activation_account
    FOREIGN KEY (account_id)
    REFERENCES account(id)
    ON DELETE CASCADE
);
-- Index: Accelerate expiration-based cleanup queries
CREATE INDEX idx_account_activation_expires_at ON account_activation(expires_at);
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
docker-compose run --rm api poetry run mypy src tests
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
docker-compose run --rm api poetry run mypy src tests
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