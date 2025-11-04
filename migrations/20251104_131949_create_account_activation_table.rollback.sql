-- Rollback: Drop account_activation table
-- Description: Rollback for create_account_activation_table migration
-- Date: 2025-11-04 13:19:49

-- This rollback removes the account_activation table and its associated index.
--
-- Rollback Order:
--   1. Drop index (if exists)
--   2. Drop table (CASCADE drops foreign key constraints automatically)
--
-- Safety:
--   - IF EXISTS prevents errors if already dropped
--   - No dependent tables (account_activation has no children)
--   - Foreign key from account_activation to account is dropped with table

-- Drop index first (PostgreSQL automatically drops with table, but explicit is clearer)
DROP INDEX IF EXISTS idx_account_activation_expires_at;

-- Drop table (CASCADE is optional here since no dependent objects exist)
DROP TABLE IF EXISTS account_activation CASCADE;