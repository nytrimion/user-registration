# Pull Requests Roadmap

Incremental development plan following **vertical feature slices**. Each PR delivers a complete, testable increment of functionality.

## Status Legend
- ⏳ Pending
- 🚧 In Progress
- ✅ Completed
- ⏭️ Skipped

---

## Infrastructure Foundation

### Docker Infrastructure ⏳
**Branch:** `feat/docker-setup`

Setup containerized development environment.

**Deliverables:**
- docker-compose.yml, Dockerfile, requirements.txt, .dockerignore, src/ structure

---

### Code Quality Tools ⏳
**Branch:** `feat/code-quality`

Configure black, ruff, mypy.

**Deliverables:**
- pyproject.toml, requirements-dev.txt

---

### Testing Framework ⏳
**Branch:** `feat/testing-framework`

Setup pytest with unit/integration structure.

**Deliverables:**
- pytest.ini, conftest.py, tests/ structure

---

### GitHub Actions CI ⏳
**Branch:** `feat/ci-pipeline`

Automate quality checks and tests on PRs.

**Deliverables:**
- .github/workflows/ci.yml running quality tools + tests

---

### FastAPI Foundation ⏳
**Branch:** `feat/fastapi-setup`

Basic FastAPI app with health check.

**Deliverables:**
- src/main.py, config.py, GET /health endpoint + test

---

## Feature: Account Creation

### Domain - Account Creation Value Objects ⏳
**Branch:** `feat/account-creation-value-objects`

Email and Password value objects for account creation.

**Deliverables:**
- Email, Password VOs + validation + unit tests

---

### Domain - Account Entity ⏳
**Branch:** `feat/account-entity`

Account aggregate root with creation logic.

**Deliverables:**
- Account entity with create() factory + unit tests

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