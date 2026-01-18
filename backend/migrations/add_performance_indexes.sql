-- Performance Indexes for Student Academic Tracker
-- 
-- This script creates indexes to optimize common database queries.
-- Expected improvement: 5-10x faster queries for student lookups, 
-- academic records, and subject queries.
--
-- Safe to run multiple times (uses IF NOT EXISTS).
--
-- Usage:
--   psql -U studentadmin -d student_tracker -f migrations/add_performance_indexes.sql

-- ============================================================================
-- STUDENT LOOKUP INDEXES
-- ============================================================================

-- Index for student_id lookups (used in authentication and profile queries)
CREATE INDEX IF NOT EXISTS idx_users_student_id ON users(student_id);

-- Index for email lookups (used in authentication)
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ============================================================================
-- ACADEMIC DATA INDEXES
-- ============================================================================

-- Composite index for user's academic terms by semester
-- Optimizes queries like: "Get all terms for user X in semester Y"
CREATE INDEX IF NOT EXISTS idx_academic_terms_user_semester 
    ON academic_terms(user_id, semester);

-- Index for all academic terms by user
-- Optimizes queries like: "Get all terms for user X"
CREATE INDEX IF NOT EXISTS idx_academic_terms_user_id 
    ON academic_terms(user_id);

-- Index for year-based queries
CREATE INDEX IF NOT EXISTS idx_academic_terms_year 
    ON academic_terms(year);

-- ============================================================================
-- SUBJECT LOOKUPS
-- ============================================================================

-- Index for subjects by term
-- Optimizes queries like: "Get all subjects for term X"
CREATE INDEX IF NOT EXISTS idx_subjects_term_id ON subjects(term_id);

-- Index for subject code lookups
CREATE INDEX IF NOT EXISTS idx_subjects_code ON subjects(subject_code);

-- ============================================================================
-- STUDENT PROFILE INDEXES
-- ============================================================================

-- Composite index for user and branch
-- Optimizes queries like: "Get all students in branch X"
CREATE INDEX IF NOT EXISTS idx_student_profiles_user_branch 
    ON student_profiles(user_id, branch);

-- Index for branch filtering
CREATE INDEX IF NOT EXISTS idx_student_profiles_branch 
    ON student_profiles(branch);

-- Index for semester filtering  
CREATE INDEX IF NOT EXISTS idx_student_profiles_semester 
    ON student_profiles(semester);

-- ============================================================================
-- ANALYZE TABLES
-- ============================================================================

-- Update table statistics for query planner optimization
ANALYZE users;
ANALYZE student_profiles;
ANALYZE academic_terms;
ANALYZE subjects;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Show created indexes
\echo ''
\echo '========================================='
\echo 'CREATED INDEXES'
\echo '========================================='

SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_indexes
JOIN pg_class ON pg_class.relname = indexname
WHERE schemaname = 'public'
    AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;

\echo ''
\echo '========================================='
\echo 'TABLE SIZES'
\echo '========================================='

SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as indexes_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

\echo ''
\echo '✅ Indexes created successfully!'
\echo ''
