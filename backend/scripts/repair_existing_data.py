#!/usr/bin/env python3
"""
repair_existing_data.py — Data cleanup script for SATA project.

Fixes:
  1. Duplicate subjects (from re-running inserts) -> DELETES duplicates, keeps latest.
  2. 8,840 orphaned students missing new columns -> UPDATES from CSV.
  3. AI&ML vs AIML naming mismatch -> UPDATES to AIML.

Usage:
    cd backend
    python scripts/repair_existing_data.py
"""

import csv
import os
import sys
import time
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

BACKGROUND_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BACKGROUND_DIR / ".env"
STUDENTS_CSV = BACKGROUND_DIR.parent / "students.csv"

load_dotenv(ENV_PATH)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("[!] DATABASE_URL not found in .env — aborting.")
    sys.exit(1)


def str_to_bool(val: str) -> bool:
    return val.strip().lower() in ("true", "1", "yes")


def main() -> None:
    print("=" * 70)
    print("  SATA — Database Repair & Cleanup")
    print("=" * 70)

    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        cur = conn.cursor()
    except Exception as e:
        print(f"[!] DB Connection Failed: {e}")
        sys.exit(1)

    # ──────────────────────────────────────────────────────────────────────────
    # PROBLEM 1: Duplicate Subjects (Delete older duplicates, keep newest)
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[1] Cleaning up duplicate subjects…")
    start = time.time()
    try:
        cur.execute("""
            WITH duplicates AS (
                SELECT id,
                       ROW_NUMBER() OVER(
                           PARTITION BY term_id, subject_code 
                           ORDER BY created_at DESC, id DESC
                       ) as rnum
                FROM subjects
            )
            DELETE FROM subjects 
            WHERE id IN (
                SELECT id FROM duplicates WHERE rnum > 1
            );
        """)
        deleted_count = cur.rowcount
        conn.commit()

        cur.execute("SELECT COUNT(*) FROM subjects")
        remaining = cur.fetchone()[0]
        
        print(f"  ✓ Deleted {deleted_count:,} duplicate subjects.")
        print(f"  ✓ Subjects remaining: {remaining:,}")

        # Recompute GPA heavily if any duplicates existed
        if deleted_count > 0:
            print("  Recomputing GPA for all terms…")
            cur.execute("""
                WITH term_gpa AS (
                    SELECT 
                        s.term_id,
                        SUM(
                            CASE s.grade
                                WHEN 'O'  THEN 10
                                WHEN 'A+' THEN 9
                                WHEN 'A'  THEN 8
                                WHEN 'B+' THEN 7
                                WHEN 'B'  THEN 6
                                WHEN 'C'  THEN 5
                                WHEN 'D'  THEN 4
                                ELSE 0 
                            END * s.credits
                        ) / NULLIF(SUM(s.credits), 0) as new_gpa
                    FROM subjects s
                    GROUP BY s.term_id
                )
                UPDATE academic_terms at
                SET gpa = COALESCE(tg.new_gpa, 0.0), updated_at = NOW()
                FROM term_gpa tg
                WHERE at.id = tg.term_id 
                  AND abs(at.gpa - COALESCE(tg.new_gpa, 0.0)) > 0.01;
            """)
            updated_gpas = cur.rowcount
            conn.commit()
            print(f"  ✓ Recomputed & updated GPA for {updated_gpas:,} terms.")

        print(f"  (Time: {time.time()-start:.1f}s)")

    except Exception as e:
        conn.rollback()
        print(f"  [!] Failed: {e}")


    # ──────────────────────────────────────────────────────────────────────────
    # PROBLEM 2: 8,840 Students Missing New Columns
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[2] Updating missing columns from students.csv…")
    start = time.time()
    try:
        if not STUDENTS_CSV.exists():
            raise FileNotFoundError(f"{STUDENTS_CSV} not found.")

        # Pre-load {student_id -> user_id}
        cur.execute("SELECT student_id, id FROM users")
        sid_to_uid = {row[0]: row[1] for row in cur.fetchall()}

        update_batch = []
        rows_not_found = 0

        with open(STUDENTS_CSV, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for raw in reader:
                sid = raw["student_id"].strip()
                if sid not in sid_to_uid:
                    rows_not_found += 1
                    continue
                
                uid = sid_to_uid[sid]
                
                dept   = raw["department"].strip()
                sem    = int(raw["current_semester"])
                b_year = int(raw["batch_year"]) if raw.get("batch_year", "").strip() else None
                perf   = raw.get("performance_status", "").strip() or None
                blogs  = int(raw.get("backlog_count", 0) or 0)
                active = str_to_bool(raw.get("active_backlog", "False"))
                cgpa   = float(raw["cgpa"]) if raw.get("cgpa", "").strip() else None

                # (uid, dept, sem, b_year, perf, blogs, active, cgpa)
                update_batch.append((
                    uid, dept, sem, b_year, perf, blogs, active, cgpa
                ))

        if update_batch:
            execute_values(
                cur,
                """
                UPDATE student_profiles AS sp
                SET department = v.dept,
                    semester = v.sem::int,
                    batch_year = v.b_year::int,
                    performance_status = v.perf,
                    backlog_count = v.blogs::int,
                    active_backlog = v.active::boolean,
                    cgpa = v.cgpa::numeric
                FROM (VALUES %s) AS v(uid, dept, sem, b_year, perf, blogs, active, cgpa)
                WHERE sp.user_id = v.uid::uuid
                """,
                update_batch,
                template="(%s, %s, %s, %s, %s, %s, %s, %s)",
                page_size=500
            )
            conn.commit()
            
        print(f"  ✓ Updated {len(update_batch):,} student profiles.")
        if rows_not_found:
            print(f"  ⚠ {rows_not_found:,} rows in CSV were not found in users table.")
        print(f"  (Time: {time.time()-start:.1f}s)")

    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
        print(f"  [!] Failed: {e}")


    # ──────────────────────────────────────────────────────────────────────────
    # PROBLEM 3: Department name inconsistency
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[3] Normalizing department names (AI&ML -> AIML)…")
    start = time.time()
    try:
        cur.execute("""
            UPDATE student_profiles 
            SET department = 'AIML' 
            WHERE department = 'AI&ML'
        """)
        renamed_count = cur.rowcount
        conn.commit()
        print(f"  ✓ Updated {renamed_count:,} profiles to AIML.")
        print(f"  (Time: {time.time()-start:.1f}s)")
    except Exception as e:
        conn.rollback()
        print(f"  [!] Failed: {e}")


    # ──────────────────────────────────────────────────────────────────────────
    # FINAL VERIFICATION
    # ──────────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  POST-REPAIR VERIFICATION")
    print("=" * 70)

    try:
        # Subjects count
        cur.execute("SELECT COUNT(*) FROM subjects")
        print(f"  Subjects count           : {cur.fetchone()[0]:,}")

        # Active backlog
        cur.execute("SELECT COUNT(*) FROM student_profiles WHERE active_backlog = true")
        print(f"  Active backlog count     : {cur.fetchone()[0]:,}")

        # Performance At Risk
        cur.execute("SELECT COUNT(*) FROM student_profiles WHERE performance_status = 'At Risk'")
        print(f"  At Risk count            : {cur.fetchone()[0]:,}")

        # Avg GPA
        cur.execute("SELECT ROUND(AVG(gpa), 2) FROM academic_terms WHERE gpa > 0")
        print(f"  Average term GPA         : {cur.fetchone()[0]}")

        # Dept distribution
        print("\n  Department Distribution:")
        cur.execute("""
            SELECT department, COUNT(*) 
            FROM student_profiles 
            GROUP BY department 
            ORDER BY count DESC
        """)
        for d, count in cur.fetchall():
            print(f"    {d:<22} : {count:,}")

    except Exception as e:
        print(f"  [!] Verification failed: {e}")

    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
