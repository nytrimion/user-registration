# Architecture Decision Records (ADR)

This document captures the key architectural decisions made during the development of the User Registration API, following the ADR format.

---

## ADR-001: Event-Driven Architecture with Synchronous MVP

**Status:** Accepted (MVP Implementation)

**Context:**

Account creation triggers email sending with activation code. Ideally, this should be asynchronous to avoid blocking HTTP responses during SMTP operations (~100-500ms latency).

**Decision:**

Use `EventDispatcher` interface with **synchronous implementation** (`InMemoryEventDispatcher`) for MVP.

**Flow:**
1. `POST /accounts` creates account and emits `AccountCreated` event
2. Event handler (`AccountCreatedHandler`) generates activation code and sends email
3. HTTP response returns **after** event handler completes (blocking)

**Rationale:**
- Demonstrates Clean Architecture (interface vs implementation decoupling)
- Avoids threading complexity for technical test scope
- Event-driven architecture proven with production-ready interface
- Faster implementation and simpler testing

**Trade-offs:**

| Aspect | Synchronous (MVP) | Asynchronous (Production) |
|--------|-------------------|---------------------------|
| HTTP Latency | +100-500ms per request | ~10ms (non-blocking) |
| Implementation Complexity | Low (no threads/queues) | Medium (Queue + Thread) |
| Testing Complexity | Low (synchronous flow) | Higher (async assertions) |
| Resilience | Email failure = HTTP 500 | Email failure isolated |

**Accepted Trade-off:** HTTP latency acceptable for MVP in exchange for faster development and simpler testing.

**Evolution Path:**

Replace `InMemoryEventDispatcher` with `AsyncEventDispatcher`:

```python
class AsyncEventDispatcher(EventDispatcher):
    """Asynchronous event dispatcher using background worker thread."""

    def __init__(self, injector: Injector):
        self._queue: Queue[object] = Queue()
        self._worker = Thread(target=self._process_events, daemon=True)
        self._worker.start()

    def dispatch(self, event: object) -> None:
        self._queue.put(event)  # Non-blocking return
```

**Benefits of Event-Driven Design:**
- **Scalability**: Decouples account creation from email delivery (survives SMTP outages)
- **Resilience**: Account creation succeeds even if email service temporarily fails
- **Observability**: Separate metrics and monitoring for account creation vs email delivery
- **Code generated just before sending**: Minimizes 60-second expiration window loss

**Migration Effort:** ~3 hours (implement AsyncEventDispatcher + update DI bindings)

---

## ADR-002: Framework-Agnostic Dependency Injection

**Status:** Accepted

**Context:**

FastAPI provides native dependency injection via `Depends()`, but it's **HTTP-request scoped only**. Event-driven architecture requires DI outside HTTP context (event handlers, CLI scripts, background jobs).

**Decision:**

Use `injector` + `fastapi-injector` instead of FastAPI's native `Depends()`.

**Rationale:**
- **Event Handlers**: `AccountCreatedHandler` runs outside HTTP context (impossible with `Depends()`)
- **Clean Architecture**: Application layer must remain framework-agnostic (no FastAPI imports)
- **Testability**: Unit test handlers with mocks without `TestClient` or `app.dependency_overrides`
- **Extensibility**: Same DI works in CLI commands, scheduled jobs, other frameworks

**Example:**

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
    def __init__(self, code_repo: AccountActivationRepository, email: EmailService):
        ...
```

**Implementation:**
- `ApplicationModule` centralizes all bindings (interfaces → implementations)
- `@inject` decorator on handler constructors for auto-wiring
- Singleton repositories (connection pooling), transient handlers (stateless)

**Documentation:** See [`docs/dependency_injection.md`](dependency_injection.md) for complete strategy and examples.

---

## ADR-003: No ORM - Raw SQL

**Status:** Accepted

**Context:**

Need to persist domain entities in PostgreSQL. ORMs (SQLAlchemy, Django ORM) provide abstraction but hide database operations.

**Decision:**

Use raw SQL queries with `psycopg2` (no ORM).

**Rationale:**
- **Explicit control** over database operations (no magic)
- **Performance transparency**: No hidden queries, predictable execution plans
- **Demonstrates raw SQL proficiency** (technical test requirement)
- **No migration auto-generation complexity**

**Benefits:**

| Benefit | Description |
|---------|-------------|
| **Performance** | No N+1 queries, explicit JOINs, predictable execution plans |
| **Debugging** | SQL logs directly usable in pgAdmin/psql for profiling |
| **Control** | Fine-grained transaction management, locking strategies (SELECT FOR UPDATE) |
| **Simplicity** | No migration auto-generation complexity (explicit SQL migrations) |

**Trade-offs Accepted:**
- ❌ More boilerplate code (manual object mapping via mappers)
- ✅ But: Total visibility and control crucial for production debugging

**Example:**

```python
# Explicit SQL query with parameterized placeholders
cursor.execute(
    """
    INSERT INTO account (id, email, password_hash, is_activated, created_at, updated_at)
    VALUES (%s, %s, %s, %s, NOW(), NOW())
    ON CONFLICT (id) DO UPDATE SET
        email = EXCLUDED.email,
        password_hash = EXCLUDED.password_hash,
        is_activated = EXCLUDED.is_activated,
        updated_at = NOW()
    """,
    (account.id.value, account.email.value, account.password.hash, account.is_activated)
)
```

**Mitigation for Boilerplate:**
- Bidirectional mappers (`to_domain`, `to_persistence`) centralize entity ↔ row conversion
- Mappers fully unit tested (100% coverage)

---

## ADR-004: DDD Encapsulation with @property

**Status:** Accepted

**Context:**

Entities must protect invariants while remaining mutable for state changes (e.g., activation).

**Decision:**

Use `@property` decorators without setters to encapsulate entity properties.

**Pattern:**

```python
# Entities are mutable but properties are encapsulated
account.activate()  # ✅ Only way to change is_activated
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

**Enforcement:**

Unit tests verify encapsulation:

```python
def test_is_activated_cannot_be_set_directly():
    account = Account.create(email, password)

    with pytest.raises(AttributeError, match="no setter"):
        account.is_activated = True  # ❌ Raises AttributeError
```

---

## ADR-005: Separate Repository for Activation Codes

**Status:** Accepted

**Context:**

Activation codes are short-lived (60s) verification tokens tied to accounts. Should they be managed by `AccountRepository` or a separate repository?

**Decision:**

Create separate `AccountActivationRepository` distinct from `AccountRepository`.

**Responsibilities:**
- **`AccountRepository`**: Manages account lifecycle (creation, retrieval, activation status)
- **`AccountActivationRepository`**: Manages short-lived verification codes (creation, validation)

**Rationale:**
- **Single Responsibility Principle** compliance
- **Independent testing** with dedicated mocks
- **Future evolution** without coupling (e.g., code history, retry mechanisms, Redis migration)

**Benefits:**

| Benefit | Description |
|---------|-------------|
| **Testability** | Mock each repository independently for faster, focused unit tests |
| **Evolvability** | Switch activation code storage (Redis, in-memory cache) without touching Account logic |
| **Performance** | Aggressive TTL/cleanup strategies for codes without impacting account data |
| **Team Collaboration** | Multiple developers can work on each repository without merge conflicts |

**Example:**

```python
# Separate repositories in use case
class ActivateAccountHandler:
    @inject
    def __init__(
        self,
        account_repo: AccountRepository,  # Account lifecycle
        activation_repo: AccountActivationRepository  # Temporary codes
    ):
        self._account_repo = account_repo
        self._activation_repo = activation_repo
```

---

## ADR-006: Activation Code Primary Key = account_id (YAGNI Principle)

**Status:** Accepted

**Context:**

Activation codes need persistence. Should they have synthetic UUID primary key or use `account_id` as PK?

**Decision:**

Use `account_id` as **primary key** (no separate UUID).

**Schema:**

```sql
CREATE TABLE account_activation (
  account_id UUID PRIMARY KEY,  -- PK (no separate id)
  code VARCHAR(4) NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  FOREIGN KEY (account_id) REFERENCES account(id) ON DELETE CASCADE
);
```

**Rationale:**
- **YAGNI** (You Aren't Gonna Need It): No code history required in current specs
- Primary key directly expresses business constraint: **1 active code per account**
- Simpler than synthetic UUID + UNIQUE(account_id) constraint
- Easy migration path if historization needed later

**Benefits:**
- **Simplicity**: No unnecessary UUID generation for temporary data
- **Explicitness**: Schema directly encodes "one code per account" rule
- **Performance**: Fewer indexes (no separate PK + UNIQUE constraint)
- **Maintainability**: Easy to evolve if requirements change (~15-minute migration)

**Future-Proofing (if needed):**

```sql
-- Migration adds UUID while preserving data chronology
ALTER TABLE account_activation ADD COLUMN id UUID DEFAULT gen_random_uuid();
-- Keep account_id as business key with UNIQUE constraint
ALTER TABLE account_activation ADD CONSTRAINT uq_account_activation_account_id UNIQUE(account_id);
```

**Trade-off Accepted:** Cannot track code history (acceptable per current requirements).

---

## ADR-007: Account Activation Workflow with Basic Auth (API Security)

**Status:** Accepted

**Context:**

Account activation requires validating a 4-digit code sent via email. Need to prevent brute-force attacks while keeping API simple (no user session management in MVP).

**Decision:**

Protect activation endpoint with **Basic Auth using API-level credentials** (not user credentials).

**Workflow:**
1. User creates account → receives email with 4-digit code and account ID
2. Client (frontend/mobile/curl) calls activation endpoint with code
3. Endpoint validates **API credentials** (Basic Auth) + activation code
4. Account transitions from inactive → active status

**API Endpoint:**

```bash
POST /accounts/{account_id}/activate
Authorization: Basic api:secret  # API credentials (configurable via env vars)
Content-Type: application/json

{
  "code": "1234"
}
```

**Validation Order:**
1. **Basic Auth (API Credentials)**: Validates request comes from authorized client (default: `api:secret`)
2. **Activation Code**: Validates 4-digit code matches account and hasn't expired (60s window)
3. **Idempotency**: Allows activation even if account already active (returns 200, not 409)

**Security Rationale:**
- **API Protection**: Basic Auth prevents malicious actors from brute-forcing activation codes
- **Separate Concerns**: API security (Basic Auth) ≠ user authentication (email + password)
- **Code in Request Body**: Avoids logging sensitive codes in browser history or server access logs
- **Time-Limited Codes**: 60-second expiration window limits attack surface
- **Configurable Credentials**: Production environments use strong `API_USERNAME` + `API_PASSWORD` env vars

**Configuration:**

```bash
# .env or environment variables
API_USERNAME=production_api_user
API_PASSWORD=strong_random_password_here
```

---

## Summary Table

| ADR | Decision | Status | Impact |
|-----|----------|--------|--------|
| ADR-001 | Synchronous Event Dispatcher | Accepted (MVP) | +100-500ms HTTP latency |
| ADR-002 | Framework-Agnostic DI | Accepted | Enables event handlers outside HTTP |
| ADR-003 | No ORM - Raw SQL | Accepted | Full database control, more boilerplate |
| ADR-004 | @property Encapsulation | Accepted | Invariant protection, explicit methods |
| ADR-005 | Separate Activation Repository | Accepted | Independent testing, evolution |
| ADR-006 | account_id as PK (YAGNI) | Accepted | Simpler schema, no history |
| ADR-007 | Basic Auth for API Security | Accepted | Brute-force protection |

---

## Evolution Roadmap

**Near-term (Next Sprint):**
- ⏳ Async Event Dispatcher (ADR-001) - 3 hours
- ⏳ Environment variable for base URL in emails - 30 min

**Mid-term (Production Release):**
- ⏳ SMTP Email Service implementation (replace LoggerEmailService) - 1 day
- ⏳ Rate limiting for activation endpoint - 2 hours
- ⏳ Monitoring/alerting for event handler failures - 3 hours

**Long-term (Post-MVP):**
- ⏳ Migration to message broker (RabbitMQ/Kafka) if needed - 1 week
- ⏳ Code history tracking if requirements change (ADR-006 revision) - 4 hours