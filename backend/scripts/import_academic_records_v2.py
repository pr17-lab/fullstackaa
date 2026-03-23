#!/usr/bin/env python3
"""
import_academic_records_v2.py — Fast bulk import of academic records for SATA.

Reads academic_records.csv (241,000 rows) and populates:
  - academic_terms  (find-or-create per user+semester+year)
  - subjects        (bulk insert via execute_values, ON CONFLICT DO NOTHING)
  - Recomputes GPA for every term after subjects are inserted.

Usage:
    cd backend
    python scripts/import_academic_records_v2.py [--truncate] [--force]
"""

import argparse
import csv
import math
import os
import sys
import time
import uuid
from collections import defaultdict
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# ─── Paths & config ───────────────────────────────────────────────────────────
BACKEND_DIR  = Path(__file__).resolve().parent.parent
ENV_PATH     = BACKEND_DIR / ".env"
CSV_PATH     = BACKEND_DIR.parent / "academic_records.csv"   # fullstack root
SUBJECT_BATCH = 1000    # rows per execute_values page
COMMIT_EVERY  = 5000    # rows between progress commits

load_dotenv(ENV_PATH)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("[!] DATABASE_URL not found in .env — aborting.")
    sys.exit(1)

if not CSV_PATH.exists():
    print(f"[!] CSV not found at {CSV_PATH} — aborting.")
    sys.exit(1)


# ─── Anna University grading ──────────────────────────────────────────────────
GRADE_POINTS = {"O": 10, "A+": 9, "A": 8, "B+": 7, "B": 6, "C": 5, "D": 4, "F": 0}

def marks_to_grade(marks: float) -> str:
    if marks >= 90: return "O"
    if marks >= 80: return "A+"
    if marks >= 70: return "A"
    if marks >= 60: return "B+"
    if marks >= 50: return "B"
    if marks >= 45: return "C"
    if marks >= 40: return "D"
    return "F"


# ─── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="Bulk import academic records.")
    parser.add_argument("--truncate", action="store_true", help="Truncate subjects and academic_terms before importing.")
    parser.add_argument("--force", action="store_true", help="Bypass idempotency warning if data exists.")
    args = parser.parse_args()

    start = time.time()

    print("=" * 60)
    print("  SATA — Academic Records Import v2")
    print(f"  CSV  : {CSV_PATH}")
    print("=" * 60)

    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    cur = conn.cursor()

    # ── 0. Check for existing data / Truncate ──────────────────────────────────
    if args.truncate:
        print("\n[0/6] Truncating existing academic_terms and subjects...")
        cur.execute("TRUNCATE subjects, academic_terms RESTART IDENTITY CASCADE;")
        conn.commit()
    else:
        cur.execute("SELECT COUNT(*) FROM subjects")
        existing_count = cur.fetchone()[0]
        if existing_count > 0 and not args.force:
            print(f"\n[!] WARNING: {existing_count:,} subjects already exist in the database.")
            print("    Running this script without --truncate might leave you with stale records if not careful.")
            print("    Please pass --force to run anyway, or --truncate to start fresh.")
            sys.exit(1)

    # Check if subjects unique constraint exists
    cur.execute("""
        SELECT COUNT(*)
        FROM pg_constraint 
        WHERE conrelid = 'subjects'::regclass 
        AND contype = 'u'
    """)
    has_subject_constraint = cur.fetchone()[0] > 0
    if not has_subject_constraint:
        print("\n[!] WARNING: 'subjects' table lacks a unique constraint on (term_id, subject_code).")
        print("    ON CONFLICT DO NOTHING will silently fail and create duplicates.")
        print("    Please run: alembic revision --autogenerate -m \"add_subjects_unique_constraint\"")
        print("    Then: alembic upgrade head")

    # ── 1. Read CSV ────────────────────────────────────────────────────────────
    print("\n[1/6] Reading CSV…")
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    total_rows = len(rows)
    print(f"      {total_rows:,} rows loaded.")

    # ── 2. Connect & pre-load lookup dicts ────────────────────────────────────
    print("\n[2/6] Connecting and pre-loading lookup tables…")
    
    # {student_id → user_id}
    cur.execute("SELECT student_id, id FROM users WHERE student_id IS NOT NULL")
    sid_to_uid: dict[str, str] = {row[0]: row[1] for row in cur.fetchall()}
    print(f"      {len(sid_to_uid):,} users loaded.")

    # {student_id → batch_year} from student_profiles
    cur.execute("""
        SELECT u.student_id, sp.batch_year
        FROM users u
        JOIN student_profiles sp ON sp.user_id = u.id
        WHERE u.student_id IS NOT NULL AND sp.batch_year IS NOT NULL
    """)
    sid_to_batch: dict[str, int] = {row[0]: row[1] for row in cur.fetchall()}
    print(f"      {len(sid_to_batch):,} batch years loaded.")

    # Pre-load existing academic_terms → {(user_id, semester) → term_id}
    cur.execute("SELECT user_id, semester, id FROM academic_terms")
    term_cache: dict[tuple, str] = {
        (str(row[0]), row[1]): str(row[2]) for row in cur.fetchall()
    }
    print(f"      {len(term_cache):,} existing academic terms cached.")

    # Pre-load existing subjects → set of (term_id, subject_code)
    cur.execute("SELECT term_id, subject_code FROM subjects")
    existing_subjects = {(str(row[0]), row[1]) for row in cur.fetchall()}
    print(f"      {len(existing_subjects):,} existing subjects cached.")

    # ── 3. Process rows ────────────────────────────────────────────────────────
    print("\n[3/6] Processing rows and building insert batches…")

    subject_batch: list[tuple]   = []
    new_term_rows:  list[tuple]  = []        # for bulk INSERT academic_terms
    # {term_id → [(grade_points, credits), …]} for GPA recompute
    term_subjects: dict[str, list[tuple[int, int]]] = defaultdict(list)

    missing_sids: set[str] = set()
    subjects_total   = 0
    terms_created    = 0
    rows_since_commit = 0
    duplicates_skipped = 0

    def flush_subjects():
        nonlocal subjects_total
        if not subject_batch:
            return
        
        conflict_clause = ""
        if has_subject_constraint:
            conflict_clause = "ON CONFLICT (term_id, subject_code) DO NOTHING"

        execute_values(
            cur,
            f"""
            INSERT INTO subjects
                (id, term_id, subject_name, subject_code, credits,
                 marks, total_marks, pass_fail, grade,
                 created_at, updated_at)
            VALUES %s
            {conflict_clause}
            """,
            subject_batch,
            template="(%s,%s,%s,%s,%s,%s,%s,%s,%s, NOW(), NOW())",
            page_size=SUBJECT_BATCH,
        )
        subjects_total += len(subject_batch)
        subject_batch.clear()

    def flush_terms():
        nonlocal terms_created
        if not new_term_rows:
            return
        execute_values(
            cur,
            """
            INSERT INTO academic_terms
                (id, user_id, semester, year, gpa, created_at, updated_at)
            VALUES %s
            ON CONFLICT (user_id, semester, year) DO NOTHING
            """,
            new_term_rows,
            template="(%s,%s,%s,%s,0.0, NOW(), NOW())",
            page_size=500,
        )
        terms_created += len(new_term_rows)
        new_term_rows.clear()

    for i, raw in enumerate(rows, 1):
        sid      = raw["student_id"].strip()
        semester = int(raw["semester"])
        marks    = float(raw["marks_obtained"])
        credits  = int(raw["credits"])
        grade    = marks_to_grade(marks)
        scode    = raw["subject_code"].strip()

        # Skip unknown students
        if sid not in sid_to_uid:
            missing_sids.add(sid)
            continue

        uid = str(sid_to_uid[sid])
        term_cache_key = (uid, semester)

        # Find-or-create academic_term
        if term_cache_key not in term_cache:
            batch_year = sid_to_batch.get(sid, 2022)
            year = batch_year + math.floor((semester - 1) / 2)
            tid  = str(uuid.uuid4())
            term_cache[term_cache_key] = tid
            new_term_rows.append((tid, uid, semester, year))

        tid = term_cache[term_cache_key]

        # Deduplicate existing subjects in memory
        subject_cache_key = (tid, scode)
        if subject_cache_key in existing_subjects:
            duplicates_skipped += 1
            continue

        # Add to memory cache to prevent duplicates within the same batch
        existing_subjects.add(subject_cache_key)

        # Accumulate subject row
        subject_batch.append((
            str(uuid.uuid4()),
            tid,
            raw["subject_name"].strip(),
            scode,
            credits,
            marks,
            int(raw.get("total_marks", 100) or 100),
            raw.get("pass_fail", "").strip() or None,
            grade,
        ))

        # Track for GPA recompute
        term_subjects[tid].append((GRADE_POINTS[grade], credits))

        rows_since_commit += 1
        if rows_since_commit >= COMMIT_EVERY:
            flush_terms()
            flush_subjects()
            conn.commit()
            rows_since_commit = 0
            pct = i / total_rows * 100
            print(f"  Progress: {i:>8,}/{total_rows:,}  ({pct:.1f}%)  "
                  f"subjects={subjects_total:,}  terms={terms_created:,}  skipped={duplicates_skipped:,}", flush=True)

    # Final flush
    flush_terms()
    flush_subjects()
    conn.commit()
    print(f"  Progress: {total_rows:,}/{total_rows:,}  (100.0%)  "
          f"subjects={subjects_total:,}  terms={terms_created:,}  skipped={duplicates_skipped:,}")

    # ── 4. Recompute GPA for all touched terms ─────────────────────────────────
    print(f"\n[4/6] Recomputing GPA for {len(term_subjects):,} terms…")

    gpa_updates: list[tuple[float, str]] = []
    for tid, subject_list in term_subjects.items():
        total_credits = sum(c for _, c in subject_list)
        if total_credits == 0:
            continue
        weighted = sum(gp * c for gp, c in subject_list)
        gpa = round(weighted / total_credits, 2)
        gpa = min(gpa, 9.99)   # fit Numeric(3,2)
        gpa_updates.append((gpa, tid))

    # Batch UPDATE in chunks of 1000
    chunk_size = 1000
    for start_i in range(0, len(gpa_updates), chunk_size):
        chunk = gpa_updates[start_i: start_i + chunk_size]
        cur.executemany(
            "UPDATE academic_terms SET gpa = %s, updated_at = NOW() WHERE id = %s",
            chunk,
        )
    conn.commit()
    print(f"      GPA updated for {len(gpa_updates):,} terms.")

    # ── 5. Final summary ───────────────────────────────────────────────────────
    elapsed = time.time() - start
    print()
    print("=" * 60)
    print("  IMPORT COMPLETE")
    print("=" * 60)
    print(f"  Total subjects inserted : {subjects_total:,}")
    print(f"  Duplicates skipped      : {duplicates_skipped:,}")
    print(f"  Academic terms created  : {terms_created:,}")
    print(f"  GPA terms recomputed    : {len(gpa_updates):,}")
    print(f"  Time taken              : {elapsed:.1f}s")

    if missing_sids:
        sample = sorted(missing_sids)[:10]
        print(f"\n  ⚠ {len(missing_sids)} student_ids not found in users table.")
        print(f"    First 10: {sample}")
    else:
        print("\n  ✓ All student_ids matched users table.")
    print("=" * 60)

    cur.close()
    conn.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        import traceback
        print(f"\n[!] Unexpected error — check if partial data needs cleanup.\n    {exc}")
        traceback.print_exc()
        sys.exit(1)
