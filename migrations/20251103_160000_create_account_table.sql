-- Migration: Create account table
-- Description: Create account table with email uniqueness and password security
-- Date: 2025-11-03 16:00:00
-- depends:

-- This migration creates the core `account` table for storing user accounts.
-- It implements the persistence layer for the Account aggregate root.
--
-- Design Decisions:
--   - UUID v7 as primary key (time-ordered, better indexing than UUID v4)
--   - Email stored in lowercase (normalized by Email value object)
--   - UNIQUE constraint on email (enforces business rule at DB level)
--   - password_hash stores bcrypt hash (never plain text)
--   - is_activated tracks account activation status (default false)
--   - created_at/updated_at for audit trail (infrastructure concern, not domain)
--
-- Performance Considerations:
--   - Index on email for fast find_by_email() queries (O(log n) vs O(n))
--   - UUID v7 provides better B-tree index performance than UUID v4
--
-- Note on updated_at:
--   No trigger used - repository explicitly sets updated_at in UPDATE queries.
--   This keeps logic visible, testable, and portable.

CREATE TABLE IF NOT EXISTS account (
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
-- This index supports the AccountRepository.find_by_email() method
-- B-tree index provides O(log n) lookup time vs O(n) sequential scan
CREATE INDEX IF NOT EXISTS idx_account_email ON account(email);

-- Comments for schema documentation
COMMENT ON TABLE account IS 'User accounts aggregate root - stores registration and authentication data';
COMMENT ON COLUMN account.id IS 'UUID v7 primary key (time-ordered for better indexing)';
COMMENT ON COLUMN account.email IS 'Normalized email address (lowercase, RFC 5322 compliant)';
COMMENT ON COLUMN account.password_hash IS 'Bcrypt password hash (never store plain text)';
COMMENT ON COLUMN account.is_activated IS 'Account activation status (requires 4-digit code verification)';
COMMENT ON COLUMN account.created_at IS 'Account creation timestamp (immutable)';
COMMENT ON COLUMN account.updated_at IS 'Last modification timestamp (set explicitly by repository on UPDATE)';