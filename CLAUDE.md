# Claude Development Configuration

## Project Context

The project is a user registration service.

### Specifications

Manage a user registration and its activation.
The API must support the following use cases:
* Create a user with an email and a password.
* Send an email to the user with a 4 digits code.
* Activate this account with the 4 digits code received. For this step, we consider a `BASIC AUTH` is enough to check if he is the right user.
* The user has only one minute to use this code. After that, an error should be raised.

### Expectations

- Python language is required.
- Code quality could go to production.
- Using frameworks is allowed only for routing, dependency injection, event dispatcher, DB connection.
- Don't use magic (ORM for example).
- Consider the SMTP server as a third party service providing an HTTP API. You can mock the call, use a local SMTP server running in a container, or simply print the 4 digits in console.
- The project must include unit and integration tests.
- The project must run within docker containers.
- README must be up to date, with running and testing instructions.

### Technical stack

- **Langage**: Python
- **Framework**: FastAPI
- **DBMS**: PostgreSQL

### Documentation References

Consider these documents as fundamental references :

- **README**: README.md
- **Project requirements**: docs/requirements.md
- **Project roadmap**: docs/roadmap.md
- **Dependency injection**: docs/dependency_injection.md

## Code Quality Standards

### Architecture Principles

- **Clean Architecture**: Clear separation between business logic, application, infrastructure and presentation layers
- **Domain Driven Design**: Implement business logic as value objects, aggregates, entities, events in Domain layer of Business Contexts
- **Clean Code**: Use clean code good practices
- **Single Responsibility**: Each class/function has one clear purpose
- **Method length**: Max 25 lines, decompose if longer
- **Component size**: Max 200 lines, split if exceeded
- **Dependency Injection**: Prefer composition over inheritance
- **Error Handling**: Explicit error types and comprehensive error handling
- **Immutability**: Prefer immutable data structures when possible

### Backend Standards

- **RESTful APIs**: Consistent HTTP methods, status codes, and response formats
- **Middleware Pattern**: Reusable middleware for authentication, validation, logging
- **Service Layer**: Business logic separated from route handlers
- **Database Layer**: Repository pattern (no ORM - raw SQL with psycopg2)
- **Input Validation**: Pydantic models for all API inputs
- **Dependency Injection**: `injector` + `fastapi-injector` for framework-agnostic DI (handlers, repositories, services injectable in HTTP routes, event handlers, CLI, tests)

## Development Workflow

### Assistant Approach

- **Explain Before Code**: Always explain the reasoning behind architectural decisions
- **Best Practice Guidance**: Highlight when code follows or violates best practices
- **Alternative Solutions**: Mention alternative approaches and their trade-offs
- **Performance Implications**: Discuss performance considerations for each implementation
- **Testing Strategy**: Suggest appropriate testing approaches for each component

### Code Generation Guidelines

#### Pre-generation Requirements

Before proposing any code:

1. **Understand the functional context** - know both "what" and "why"
2. **Design the architecture first** - structure before implementation
3. **Define contracts** - interfaces and types before logic
4. **Plan for testability** - consider how the code will be tested
5. **Consider performance implications** - especially for real-time features

#### Generation Process

1. **Types/interfaces first** - define contracts before implementation
2. **Core implementation second** - focus on main business logic
3. **Error handling third** - comprehensive error scenarios
4. **Edge cases and optimizations last** - handle exceptional scenarios
5. **Tests alongside** - suggest test cases for each component

#### Post-generation Validation

Before finalizing code:

1. **Verify naming** - does every identifier clearly express its intention?
2. **Check responsibilities** - can any method/class be split further?
3. **Eliminate redundancies** - remove unnecessary variables and abstractions
4. **Apply obvious refactorings** - improve structure and readability
5. **Review against anti-patterns** - ensure compliance with standards above

#### Docker Integration

- **Development Environment**: Docker Compose for consistent local development
- **Environment Separation**: Clear separation between development, test, and production configs
- **Service Communication**: Proper networking between containerized services

#### Review and Feedback Process

When receiving code feedback:

- **Accept rejection gracefully** - fragile or incorrect solutions should be discarded
- **Learn from manual corrections** - understand why manual fixes were preferred
- **Iterate based on critique** - use feedback to improve subsequent generations
- **Maintain code quality** - never compromise standards for speed
- **Explain reasoning** - provide rationale for architectural decisions

#### Performance Considerations

- **Memory optimization** - minimize object allocation in loops
- **Bundle size** - consider impact on frontend bundle size
- **Database queries** - optimize for N+1 problems and proper indexing
- **Real-time performance** - efficient Socket.io event handling
- **Lazy loading** - implement code splitting and lazy loading where appropriate

### Database Design

- **Schema Design**: Normalized database structure with proper relationships
- **Migration Strategy**: Safe, reversible database migrations
- **Query Optimization**: Efficient queries with proper indexing
- **Data Validation**: Both database-level and application-level validation

## Anti-patterns to Systematically Avoid

### Naming Conventions

**Banned generic names:**

- `data`, `item`, `value`, `temp`, `result`, `obj`, `info`, `stuff`

**Required naming conventions:**

- Use complete names describing business intention
- Boolean: `isValid`, `hasPermission`, `canExecute`
- Counters: `userCount`, `messageTotal`, `maxRetries`
- Actions: `createUser`, `validateInput`, `sendMessage`
- Collections: `activeUsers`, `chatMessages`, `validationRules`

### Structural Anti-patterns

- **Monolithic methods** - break down into smaller, focused methods
- **God components** - decompose into specialized components
- **Mixed concerns** - separate business logic, validation, and presentation
- **Deep nesting** - use early returns and guard clauses

### Verbosity Issues

- **Single-use variables** - prohibited unless they improve business clarity
- **Obvious explanatory variables** - eliminate redundant intermediates
- **Defensive over-commenting** - trust well-named code to be self-documenting
- **Unnecessary abstractions** - don't over-engineer simple solutions

## DDD Implementation Rules

### Bounded Context Structure

- Each BC: `domain/` → `application/contracts/` → `application/services/` → `infrastructure/`
- Core BC: shared primitives

### DDD Requirements

- **Interfaces in contracts/**: All cross-BC communication via interfaces + DTOs
- **Strong typing**: Explicit DTOs for all BC boundaries
- **Constructor injection**: Dependencies via interfaces only
- **Aggregates**: Consistency boundaries with business rules
- **Value Objects**: Immutable domain primitives

### CQRS Structure (Simplified)

For projects < 10 use cases, use **pragmatic CQRS**:

- **Commands**: Merge Command (DTO) + Handler in **same file** (`application/commands/register_account.py`)
- **Events**: Keep event handlers **separate** (`application/events/account_created_handler.py`) - different dependencies + execution context (async)
- **Rationale**: Reduces boilerplate, improves cohesion, maintains testability

**Example**:
```python
# application/commands/register_account.py
@dataclass(frozen=True)
class RegisterAccountCommand:
    email: Email
    password: Password

class RegisterAccountHandler:
    @inject
    def __init__(self, repository: AccountRepository):
        self._repository = repository
```

### Development Priorities

1. Domain entities with business logic first
2. Application contracts for BC interfaces
3. Infrastructure last (controllers, repositories)
4. Test via contracts, never internal implementations
