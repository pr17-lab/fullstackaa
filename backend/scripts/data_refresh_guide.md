# Data Refresh Guide

Complete guide for safely replacing student data with the IEEE CSV dataset.

## Overview

This guide walks you through the process of replacing existing student data with the authoritative IEEE CSV dataset (`SATA_student_main_info_10k_IEEE.csv`). The process includes automatic backup, data replacement, verification, and rollback procedures.

## Prerequisites

- PostgreSQL database running and accessible
- Backend environment configured with database credentials
- IEEE CSV file exists at: `backend/data/SATA_student_main_info_10k_IEEE.csv`
- Python environment activated (if using virtual environment)

## Scripts Overview

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `backup_student_data.py` | Backup existing data | Before any data changes (auto-called by refresh script) |
| `refresh_student_data.py` | **Main script** - Backup, truncate, import, verify | To replace data with IEEE CSV |
| `rollback_student_data.py` | Restore from backup | If refresh fails or needs to be reversed |

## Step-by-Step Execution

### Step 1: Navigate to Backend Directory

```bash
cd c:\Users\Admin\Desktop\fullstack\backend
```

### Step 2: Run Data Refresh Script

```bash
python scripts\refresh_student_data.py
```

**What this script does:**
1. ✓ Verifies IEEE CSV file exists and validates schema
2. ✓ Shows current database row counts
3. ✓ **Automatically backs up** existing data to `backups/` directory
4. ✓ Truncates `student_profiles` and `users` tables
5. ✓ Imports all 10,000 records from IEEE CSV
6. ✓ Verifies import with row counts and data integrity checks
7. ✓ Displays sample records (first 3 and last 3)

**Expected Output:**
```
================================================================================
DATA REFRESH: Replace Student Data with IEEE CSV
================================================================================

[*] Verifying CSV file: SATA_student_main_info_10k_IEEE.csv
    [+] CSV file found: SATA_student_main_info_10k_IEEE.csv
    [+] CSV contains 10,000 records
    [+] CSV schema validated

[*] Current Database Counts (Before Refresh):
    - Users: 10,000
    - Student Profiles: 10,000

================================================================================
STEP 1: BACKING UP EXISTING DATA
================================================================================
[+] Backup completed successfully

================================================================================
STEP 2: TRUNCATING EXISTING DATA
================================================================================
[+] Tables successfully truncated

================================================================================
STEP 3: IMPORTING IEEE CSV DATA
================================================================================
    Progress: 1,000/10,000 records imported...
    Progress: 2,000/10,000 records imported...
    ...
[+] Import Summary:
    - Users created: 10,000
    - Student profiles created: 10,000

================================================================================
STEP 4: VERIFYING IMPORTED DATA
================================================================================
[+] ✓ Data refresh verification PASSED

[!] IMPORTANT NEXT STEPS:
    1. Regenerate password hashes:
       cd backend
       python scripts\generate_passwords_from_student_id.py
```

### Step 3: Regenerate Password Hashes

After the refresh, password hashes must be regenerated:

```bash
python scripts\generate_passwords_from_student_id.py
```

**Expected Output:**
```
[+] Updated 10,000 password hashes
```

### Step 4: Verify Application Functionality

1. **Start Backend Server:**
   ```bash
   cd c:\Users\Admin\Desktop\fullstack\backend
   uvicorn app.main:app --reload
   ```

2. **Start Frontend Server** (in new terminal):
   ```bash
   cd c:\Users\Admin\Desktop\fullstack\frontend
   npm run dev
   ```

3. **Test Authentication:**
   - Open browser to frontend URL
   - Login with a `student_id` from IEEE CSV
   - Format: `S00001` with password `S00001@123`
   - Verify profile data displays correctly (name, branch, semester)

4. **Test API Endpoints:**
   - Navigate to dashboard, performance, and settings pages
   - Verify no errors in backend console
   - Confirm data is loading correctly

## Rollback Procedure

If the refresh fails or you need to restore the original data:

### Option 1: Rollback to Most Recent Backup

```bash
python scripts\rollback_student_data.py
```

This will automatically use the most recent backup.

### Option 2: Rollback to Specific Backup

```bash
python scripts\rollback_student_data.py 20260118_114530
```

Replace `20260118_114530` with the timestamp of the backup you want to restore.

**To list available backups:**
```bash
dir backend\backups\backup_info_*.txt
```

**Expected Rollback Output:**
```
================================================================================
ROLLBACK STUDENT DATA FROM BACKUP
================================================================================

[*] Found 1 backup(s):
    1. Timestamp: 20260118_114530

[*] Using most recent backup: 20260118_114530

================================================================================
STEP 1: CLEARING CURRENT DATA
================================================================================
[+] Tables successfully cleared

================================================================================
STEP 2: RESTORING USERS TABLE
================================================================================
[+] Restoration complete for users

================================================================================
STEP 3: RESTORING STUDENT_PROFILES TABLE
================================================================================
[+] Restoration complete for student_profiles

[+] ✓ Rollback completed successfully!
```

## Backup Files

All backups are stored in: `backend/backups/`

**File naming convention:**
- `users_backup_YYYYMMDD_HHMMSS.sql` - PostgreSQL INSERT statements for users table
- `student_profiles_backup_YYYYMMDD_HHMMSS.sql` - PostgreSQL INSERT statements for student_profiles table
- `users_backup_YYYYMMDD_HHMMSS.csv` - CSV export of users table
- `student_profiles_backup_YYYYMMDD_HHMMSS.csv` - CSV export of student_profiles table
- `student_data_backup_YYYYMMDD_HHMMSS.csv` - Combined CSV with user and profile data
- `backup_info_YYYYMMDD_HHMMSS.txt` - Backup metadata and file listing

## Troubleshooting

### Issue: CSV file not found

**Error:**
```
[!] ERROR: CSV file not found at backend/data/SATA_student_main_info_10k_IEEE.csv
```

**Solution:**
```bash
# Verify file exists
dir backend\data\SATA_student_main_info_10k_IEEE.csv
```

### Issue: Database connection failed

**Error:**
```
[!] ERROR: could not connect to server
```

**Solution:**
```bash
# Verify PostgreSQL is running
docker ps

# If not running, start it
docker-compose up -d postgres
```

### Issue: Row count mismatch after import

**Error:**
```
[!] User count mismatch: expected 10000, got 9850
```

**Solution:**
1. Check for errors in the import output
2. Verify CSV file integrity:
   ```bash
   python -c "import pandas as pd; print(len(pd.read_csv('backend/data/SATA_student_main_info_10k_IEEE.csv')))"
   ```
3. If issues persist, rollback and investigate CSV data

### Issue: Password generation script not found

**Error:**
```
[!] ERROR: scripts\generate_passwords_from_student_id.py not found
```

**Solution:**
This script should exist from previous setup. If missing, re-create it or use the student_id + "@123" format for passwords.

## Post-Refresh Checklist

- [ ] Data refresh completed successfully (10,000 users + profiles)
- [ ] Password hashes regenerated for all users
- [ ] Backend server starts without errors
- [ ] Frontend server starts without errors
- [ ] Authentication works with sample student_id
- [ ] User profile displays correct data from IEEE CSV
- [ ] Dashboard and performance pages load correctly
- [ ] No 500 errors in backend logs
- [ ] Backup files saved in `backend/backups/` directory

## Important Notes

> [!WARNING]
> **Active Sessions**: Any users logged in during the refresh will be logged out and need to re-authenticate with their student_id.

> [!IMPORTANT]
> **Password Format**: After password regeneration, the login format is:
> - **Username**: `student_id` (e.g., `S00001`)
> - **Password**: `{student_id}@123` (e.g., `S00001@123`)

> [!CAUTION]
> **Backup Retention**: Keep backups for at least 7 days before deleting. They are your safety net for rollback operations.

## Quick Command Reference

```bash
# Full data refresh (recommended)
cd backend
python scripts\refresh_student_data.py
python scripts\generate_passwords_from_student_id.py

# Manual backup only
python scripts\backup_student_data.py

# Rollback to most recent backup
python scripts\rollback_student_data.py

# Rollback to specific backup
python scripts\rollback_student_data.py 20260118_114530

# Verify row counts
python -c "from app.models import User, StudentProfile; from app.core.database import SessionLocal; session = SessionLocal(); print(f'Users: {session.query(User).count()}'); print(f'Profiles: {session.query(StudentProfile).count()}')"
```
