"""
Domain events for account bounded context.

Events represent past occurrences in the domain that are of interest to
other parts of the system. Events are immutable and should be named in
past tense.

Design Principles:
    - Immutable (@dataclass(frozen=True))
    - Past tense naming (AccountCreated, not CreateAccount)
    - Carry only essential data (no business logic)
    - Domain layer only (no infrastructure dependencies)
"""
