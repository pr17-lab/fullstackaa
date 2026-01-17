-- Backup Users Table Before Migration
-- Creates a timestamped backup table with all existing user data
-- This provides rollback capability in case migration fails

-- Generate backup table name with timestamp
-- Format: users_backup_YYYYMMDD_HHMMSS
-- Note: Execute this via Python to generate dynamic timestamp

-- Example: users_backup_20260117_142200
DO $$
DECLARE
    backup_table_name TEXT;
BEGIN
    backup_table_name := 'users_backup_' || to_char(now(), 'YYYYMMDD_HH24MISS');
    
    -- Create backup table with same schema as users
    EXECUTE format('CREATE TABLE %I AS TABLE users', backup_table_name);
    
    -- Verify backup was created successfully
    RAISE NOTICE 'Backup created: %', backup_table_name;
    RAISE NOTICE 'Records backed up: %', (SELECT COUNT(*) FROM users);
END $$;

-- Query to verify backup
-- SELECT table_name FROM information_schema.tables 
-- WHERE table_name LIKE 'users_backup_%' 
-- ORDER BY table_name DESC LIMIT 1;
