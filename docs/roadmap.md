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

### Domain - Account Repository Interface ✅
**Branch:** `feat/account-repository-interface`

Repository contract for account persistence.

**Completed:**
- ✅ AccountRepository ABC with create() method
- ✅ Repository interface in domain layer (no technical dependencies)
- ✅ Documented DDD principles (repository per aggregate root)
- ✅ Business rules documented (email/ID uniqueness enforcement)
- ✅ Refactored Account.account_id → Account.id for simplicity

---

### Application - RegisterAccount Use Case ✅
**Branch:** `feat/register-account-use-case`

Use case orchestrating account registration with email uniqueness validation.

**Completed:**
- ✅ `RegisterAccountCommand` (immutable DTO with Email + Password VOs)
- ✅ `RegisterAccountHandler` (CQRS handler with @inject decorator)
- ✅ `EmailAlreadyExistsError` domain exception
- ✅ `AccountRepository.find_by_email()` interface method
- ✅ 8 unit tests with repository mocks (100% coverage)
- ✅ Check-Then-Insert pattern (race condition documented)
- ✅ Framework-agnostic handler (no FastAPI dependency)
- ✅ Dependencies: `injector` + `fastapi-injector` added

---

### Infrastructure - PostgresAccountRepository Implementation ✅
**Branch:** `feat/account-repository-implementation`

PostgreSQL repository implementation with database migration and integration tests.

**Rationale:**
Merged "Database Migration" and "AccountRepository" PRs into single vertical
slice. This allows immediate validation of SQL schema through repository tests,
avoiding late discovery of migration issues and ensuring atomicity.

**Completed:**
- ✅ SQL migration script (account table: UUID v7, UNIQUE email, audit columns)
- ✅ Yoyo-migrations setup (Python wrapper, rollback support, CI integration)
- ✅ Database connection pool (PostgresConnectionFactory with ThreadedConnectionPool)
- ✅ DatabaseConnectionFactory interface (injectable, testable)
- ✅ InfrastructureModule (DI bindings for shared infrastructure)
- ✅ 6 integration tests for connection pool (96% coverage)
- ✅ Docker layer optimization (scripts → migrations → src)
- ✅ README documentation (Database Migrations section)
- ✅ CI pipeline integration (migrations before tests)
- ✅ PostgresAccountRepository implementation (create, find_by_email methods with raw SQL)
- ✅ Bidirectional mappers (Account entity ↔ DB row with type conversions)
- ✅ 8 unit tests for mappers (100% coverage, UUID/string conversion validation)
- ✅ 6 integration tests for repository (100% coverage, real PostgreSQL)
- ✅ AccountModule (DI bindings for account bounded context)
- ✅ Auto-commit strategy (pragmatic approach: repository commits automatically)
- ✅ All quality tools passing (Black, Ruff, Mypy on src + tests)

**Implementation Order:**
1. ✅ Migration SQL + connection pool setup (3 commits)
2. ✅ Repository implementation with raw SQL queries (psycopg2, parameterized)
3. ✅ Entity-to-row mappers (preserving value objects, UUID↔string conversion)
4. ✅ Integration tests (pytest + Docker PostgreSQL service, 6 tests)
5. ✅ Unit tests for mappers (8 tests, round-trip validation)

---

### Infrastructure - POST /accounts Endpoint ✅
**Branch:** `feat/post-accounts-endpoint`

API endpoint for account creation.

**Completed:**
- ✅ RegisterAccountRequest Pydantic model (email, password validation)
- ✅ account_controller.py with POST /accounts route (FastAPI APIRouter)
- ✅ Dependency injection integration (AccountModule, RegisterAccountHandler)
- ✅ Error handling (400 domain validation, 409 duplicate email, 422 Pydantic)
- ✅ OpenAPI documentation with response examples (400, 409, 422)
- ✅ 8 integration tests (201 success, duplicate email, validation errors, whitespace trimming)
- ✅ All quality tools passing (Black, Ruff, Mypy on src + tests)
- ✅ 100 tests passing, 98% project coverage

**Implementation Notes:**
- HTTP 201 Created with empty response body (no Location header)
- CQRS handler remains void (no return value)
- Two-layer validation: Pydantic (422) + Domain VOs (400)
- Email normalization and whitespace trimming validated in tests

---

## Feature: Account Activation

### Infrastructure - Event System & AccountCreated Event ✅
**Branch:** `feat/account-created-event`

Complete event system with AccountCreated event emission after account creation.

**Completed:**
- ✅ AccountCreated domain event (immutable dataclass with account_id, email, occurred_at)
- ✅ EventDispatcher interface (abstract base class in shared domain)
- ✅ InMemoryEventDispatcher implementation (synchronous dispatcher with handler registry)
- ✅ RegisterAccountHandler updated to inject EventDispatcher and dispatch AccountCreated event
- ✅ Unit tests for event emission and dispatcher (3 tests for event, 5 tests for dispatcher, 1 new test for handler)
- ✅ DI integration (EventDispatcher registered as singleton in InfrastructureModule)
- ✅ Documentation updated (README.md, docs/dependency_injection.md with ADR)

**Architecture:**
- Handler emits event directly (not stored in entity)
- EventDispatcher resolves handlers via injector (works outside HTTP context)
- Synchronous implementation for MVP (ADR documented for future async evolution)
- Following docs/dependency_injection.md event handler pattern

---

### Domain - Account Activation (VO + Entity + Repository Interface) ✅
**Branch:** `feat/activation-code-domain`

Complete domain layer for account activation workflow.

**Rationale:**
Merged ActivationCode VO and Repository interface PRs into single domain slice.
This ensures atomic domain logic coherence (VO + Entity + Repository contract
validated together) and facilitates review of complete business rules.

**Completed:**
- ✅ ActivationCode VO (4-digit code generation and validation with CODE_LENGTH constant)
- ✅ AccountActivation Entity (composite PK account_id, @classmethod factory, encapsulation)
- ✅ AccountActivationRepository interface (save with UPSERT, find_by_account_id, delete)
- ✅ 14 unit tests for ActivationCode VO (100% coverage)
- ✅ 12 unit tests for AccountActivation entity (100% coverage)
- ✅ All quality tools passing (Black, Ruff, Mypy strict mode)

**Architecture:**
- AccountActivation = Entity with composite PK (account_id)
- ActivationCode = VO (immutable, no identity, part of entity)
- Expiration logic in entity (60 seconds from creation)
- Repository persists entity (DDD pattern: Repository → Entity, not VO)
- PostgreSQL UPSERT support (INSERT ... ON CONFLICT ... DO UPDATE)

---

### Infrastructure - PostgresAccountActivationRepository Implementation ⏳
**Branch:** `feat/account-activation-repository-implementation`

PostgreSQL repository implementation with database migration and integration tests.

**Rationale:**
Merged "Database Migration" and "AccountActivationRepository" PRs into single vertical
slice. This allows immediate validation of SQL schema through repository tests,
avoiding late discovery of migration issues and ensuring atomicity. Same pattern
as PostgresAccountRepository (line 142-150).

**Deliverables:**
- SQL migration script (account_activation_code table: account_id PK, code, expires_at, audit columns)
- PostgresAccountActivationRepository implementation (save, find_by_account_id, delete methods with raw SQL)
- Bidirectional mappers (AccountActivation entity ↔ DB row with type conversions)
- Unit tests for mappers (100% coverage, AccountId/string conversion validation)
- Integration tests for repository (100% coverage, real PostgreSQL)
- All quality tools passing (Black, Ruff, Mypy on src + tests)

**Implementation Order:**
1. Migration SQL + connection pool reuse (existing infrastructure)
2. Repository implementation with raw SQL queries (psycopg2, parameterized)
3. Entity-to-row mappers (preserving value objects, expiration timestamp handling)
4. Integration tests (pytest + Docker PostgreSQL service)
5. Unit tests for mappers (round-trip validation)

---

### Infrastructure - Email Service ⏳
**Branch:** `feat/email-service`

Email service abstraction with console implementation.

**Deliverables:**
- EmailService interface + ConsoleEmailService + unit tests

---

### Application - AccountCreatedHandler (Event Handler) ⏳
**Branch:** `feat/account-created-handler`

Event handler that reacts to AccountCreated event by generating activation code and sending email.

**Deliverables:**
- AccountCreatedHandler (injects ActivationCodeRepository + EmailService)
- Generates 4-digit activation code with 60s expiration
- Sends email with code (console output for now)
- Unit tests with mocked dependencies
- Register handler in EventDispatcher

**Dependencies:**
- Requires: ActivationCode VO, ActivationCodeRepository, EmailService
- Called by: EventDispatcher when AccountCreated is dispatched

---

### Application - ActivateAccount Use Case ⏳
**Branch:** `feat/activate-account-use-case`

Use case for account activation with code verification.

**Deliverables:**
- ActivateAccount use case + unit tests with mocks

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