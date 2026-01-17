-- Verification Queries for Migration Success
-- Run after migration to validate password hash integrity

-- ============================================================
-- 1. Check for NULL password hashes
-- ============================================================
SELECT 
    COUNT(*) as users_with_null_hash,
    (SELECT COUNT(*) FROM users) as total_users
FROM users 
WHERE password_hash IS NULL;

-- Expected: users_with_null_hash = 0


-- ============================================================
-- 2. Verify bcrypt hash format
-- ============================================================
SELECT 
    COUNT(*) as valid_bcrypt_hashes,
    (SELECT COUNT(*) FROM users) as total_users
FROM users 
WHERE password_hash IS NOT NULL 
AND password_hash LIKE '$2b$%';

-- Expected: valid_bcrypt_hashes = total_users


-- ============================================================
-- 3. Check password hash length
-- ============================================================
SELECT 
    MIN(LENGTH(password_hash)) as min_length,
    MAX(LENGTH(password_hash)) as max_length,
    AVG(LENGTH(password_hash))::INT as avg_length
FROM users 
WHERE password_hash IS NOT NULL;

-- Expected: All values should be 60 (bcrypt standard length)


-- ============================================================
-- 4. Check password column capacity
-- ============================================================
SELECT 
    column_name,
    data_type,
    character_maximum_length
FROM information_schema.columns
WHERE table_name = 'users' 
AND column_name = 'password_hash';

-- Expected: character_maximum_length >= 255 (bcrypt needs 60 chars)


-- ============================================================
-- 5. Sample password hashes
-- ============================================================
SELECT 
    student_id,
    email,
    LEFT(password_hash, 30) as hash_preview,
    LENGTH(password_hash) as hash_length
FROM users
WHERE password_hash IS NOT NULL
ORDER BY RANDOM()
LIMIT 5;

-- Expected: All hashes start with $2b$ and have length 60


-- ============================================================
-- 6. Migration coverage
-- ============================================================
SELECT 
    COUNT(*) as total_users,
    COUNT(password_hash) as users_with_hash,
    COUNT(*) - COUNT(password_hash) as missing_hashes,
    ROUND(100.0 * COUNT(password_hash) / COUNT(*), 2) as coverage_percentage
FROM users;

-- Expected: coverage_percentage = 100.00


-- ============================================================
-- 7. Check backup table exists
-- ============================================================
SELECT table_name 
FROM information_schema.tables 
WHERE table_name LIKE 'users_backup_%' 
ORDER BY table_name DESC 
LIMIT 1;

-- Expected: Should show the latest backup table name
