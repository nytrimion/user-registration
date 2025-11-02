# Development Roadmap

Incremental development plan following **vertical feature slices**.

This roadmap tracks all planned pull requests (PRs) for the project. Each PR delivers a complete, testable increment of functionality, ensuring the codebase remains in a deployable state at all times.

## Status Legend
- ⏳ Pending
- 🚧 In Progress
- ✅ Completed
- ⏭️ Skipped

---

## Infrastructure Foundation

### Docker Infrastructure ✅
**Branch:** `docker-setup`

Setup containerized development environment with Poetry dependency management.

**Completed:**
- ✅ Docker Compose with API + PostgreSQL services
- ✅ Multi-stage Dockerfile (development + production targets)
- ✅ Poetry 1.8.4 for dependency management
- ✅ pyproject.toml with all dependencies and tool configurations
- ✅ Code quality tools: black, ruff, mypy (configured)
- ✅ Testing tools: pytest, pytest-asyncio, pytest-cov, httpx (configured)
- ✅ Basic FastAPI app with GET /health endpoint

---

### Testing Structure ✅
**Branch:** `feat/testing-structure`

Create test directory structure and shared fixtures.

**Completed:**
- ✅ tests/ directory structure (unit/, integration/, e2e/)
- ✅ conftest.py with shared fixtures (TestClient, base URL)
- ✅ First integration test for /health endpoint (3 tests, 100% coverage)
- ✅ All quality tools validated (black, ruff, mypy, pytest)

---

### GitHub Actions CI ✅
**Branch:** `ci/github-pipeline`

Automate quality checks and tests on PRs + production-ready environment configuration.

**Completed:**
- ✅ .github/workflows/ci.yml with 4 parallel jobs
- ✅ Lint job: Black (formatting) + Ruff (linting)
- ✅ Type-check job: Mypy with strict mode
- ✅ Test job: Pytest + Coverage + PostgreSQL service
- ✅ Docker build job: Validation of dev & prod images
- ✅ Poetry venv caching for faster builds
- ✅ Codecov integration for coverage reporting
- ✅ Environment variables with .env.example (no hardcoded secrets)
- ✅ docker-compose.yml using ${VAR:-default} syntax

---

### Health Check DDD Refactoring ✅
**Branch:** `refactor/health-check-ddd`

Refactor /health endpoint into proper DDD structure with shared bounded context.

**Completed:**
- ✅ src/shared/infrastructure/http/ structure with documented __init__.py files
- ✅ Health check controller using FastAPI APIRouter pattern
- ✅ Refactored main.py to use include_router (proper dependency injection)
- ✅ Tests reorganized to mirror source structure (tests/integration/shared/...)
- ✅ All integration tests passing with 100% coverage maintained
- ✅ Example of DDD structure for future bounded contexts (account, auth, etc.)

---

## Feature: Account Creation

### Domain - Account Creation Value Objects ✅
**Branch:** `feat/account-creation-value-objects`

Email, Password, and AccountId value objects for account creation.

**Completed:**
- ✅ Email VO with email-validator library (RFC 5322 compliance, lowercase normalization)
- ✅ Password VO with bcrypt hashing and Self type hint
- ✅ AccountId VO inheriting from shared UuidV7 abstract base class
- ✅ UuidV7 abstract base class in shared domain (UUID v7 validation and factory methods)
- ✅ 42 unit tests with 100% coverage on all value objects
- ✅ Python 3.14 upgrade for native uuid.uuid7() support

---

### Domain - Account Entity ✅
**Branch:** `feat/account-entity`

Account aggregate root with creation logic and DDD encapsulation.

**Completed:**
- ✅ Account entity with @dataclass + @property for encapsulation
- ✅ Account.create() factory method with UUID v7 generation
- ✅ activate() method with business rule enforcement
- ✅ Entity identity pattern (__eq__ by account_id, __hash__ support)
- ✅ 19 unit tests with 100% coverage on Account entity
- ✅ Encapsulation validated: properties raise AttributeError on direct modification

---

### Domain - Account Repository Interface ⏳
**Branch:** `feat/account-repository-interface`

Repository contract for account persistence.

**Deliverables:**
- AccountRepository interface (save, find_by_email, find_by_id)

---

### Application - RegisterAccount Use Case ⏳
**Branch:** `feat/register-account-use-case`

Use case orchestrating account registration.

**Deliverables:**
- RegisterAccount use case + unit tests with mocks

---

### Infrastructure - Database Migration (Account) ⏳
**Branch:** `feat/account-table-migration`

SQL schema for account table.

**Deliverables:**
- Migration script, connection pool, account table

---

### Infrastructure - AccountRepository ⏳
**Branch:** `feat/account-repository`

Repository implementation with raw SQL.

**Deliverables:**
- AccountRepository + mappers + integration tests

---

### Infrastructure - POST /accounts Endpoint ⏳
**Branch:** `feat/post-accounts-endpoint`

API endpoint for account creation.

**Deliverables:**
- POST /accounts controller + request/response models + integration tests

---

## Feature: Account Activation

### Domain - Account Created Event ⏳
**Branch:** `feat/account-created-event`

Domain event emitted after account creation.

**Deliverables:**
- AccountCreated event + update RegisterAccount to emit event

---

### Domain - ActivationCode Value Object ⏳
**Branch:** `feat/activation-code-vo`

4-digit code with expiration logic.

**Deliverables:**
- ActivationCode VO + generation + expiration logic + unit tests

---

### Domain - ActivationCodeRepository Interface ⏳
**Branch:** `feat/activation-code-repository-interface`

Repository contract for activation codes.

**Deliverables:**
- ActivationCodeRepository interface (save, find_by_account_id)

---

### Infrastructure - Database Migration (Activation Code) ⏳
**Branch:** `feat/activation-code-table-migration`

SQL schema for activation_code table.

**Deliverables:**
- Migration script, account_activation_code table

---

### Infrastructure - PostgresActivationCodeRepository ⏳
**Branch:** `feat/postgres-activation-code-repository`

Repository implementation for activation codes.

**Deliverables:**
- PostgresActivationCodeRepository + integration tests

---

### Infrastructure - Email Service ⏳
**Branch:** `feat/email-service`

Email service abstraction with console implementation.

**Deliverables:**
- EmailService interface + ConsoleEmailService + unit tests

---

### Application - ActivateAccount Use Case ⏳
**Branch:** `feat/activate-account-use-case`

Use case for account activation with code verification.

**Deliverables:**
- ActivateAccount use case + unit tests with mocks

---

### Infrastructure - Event Dispatcher & Handler ⏳
**Branch:** `feat/event-dispatcher`

Event system triggering code generation and email.

**Deliverables:**
- Event dispatcher + AccountCreatedHandler (generates code + sends email) + tests

---

### Infrastructure - POST /accounts/activate Endpoint ⏳
**Branch:** `feat/post-accounts-activate-endpoint`

API endpoint for account activation.

**Deliverables:**
- POST /accounts/activate controller + Basic Auth + integration tests

---

## Finalization

### End-to-End Testing ⏳
**Branch:** `feat/e2e-tests`

Complete user journey validation.

**Deliverables:**
- E2E tests (creation → email → activation)
- Code expiration scenarios
- Error cases

---

### Documentation & Architecture ⏳
**Branch:** `feat/final-documentation`

Polish documentation and diagrams.

**Deliverables:**
- Updated README
- Improved architecture diagram
- API documentation

---

## Notes

- Each PR builds on previous ones (sequential dependencies)
- All PRs include tests before merge
- CI must pass on all PRs
- Small, reviewable increments (~20min review time)