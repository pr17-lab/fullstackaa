#!/usr/bin/env python3
"""
import_students_v2.py — Fast batch import for SATA project.

Optimizations:
  1. Parallel bcrypt hashing via multiprocessing.Pool
  2. execute_values bulk inserts (1 SQL call per table)
  3. Single transaction with pre-fetched duplicate set
  4. All UUIDs generated in Python before DB work

Usage:
    cd backend
    python scripts/import_students_v2.py
"""

import csv
import os
import sys
import uuid
import time
from collections import defaultdict
from multiprocessing import Pool, cpu_count
from pathlib import Path

import bcrypt
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# ─── Paths & config ───────────────────────────────────────────────────────────
BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_PATH    = BACKEND_DIR / ".env"
CSV_PATH    = BACKEND_DIR.parent / "students.csv"   # fullstack root
BATCH_COST  = 6          # bcrypt rounds — fast for bulk seed (default 12 = slow)

load_dotenv(ENV_PATH)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("[!] DATABASE_URL not found in .env — aborting.")
    sys.exit(1)

if not CSV_PATH.exists():
    print(f"[!] CSV not found at {CSV_PATH} — aborting.")
    sys.exit(1)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _hash_one(student_id: str) -> tuple[str, str]:
    """Hash one password — runs in a worker process."""
    plain = f"{student_id}@123"
    hashed = bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=BATCH_COST)).decode()
    return student_id, hashed


def parallel_hash(student_ids: list[str]) -> dict[str, str]:
    """Hash all passwords in parallel; return {student_id: hash}."""
    workers = max(1, cpu_count())
    total   = len(student_ids)
    print(f"  Hashing {total:,} passwords on {workers} CPU cores (rounds={BATCH_COST})…")

    results: dict[str, str] = {}
    done = 0
    with Pool(workers) as pool:
        for sid, hashed in pool.imap_unordered(_hash_one, student_ids, chunksize=50):
            results[sid] = hashed
            done += 1
            if done % 1000 == 0 or done == total:
                pct = done / total * 100
                print(f"    [{done:>6,}/{total:,}]  {pct:5.1f}%", end="\r", flush=True)

    print()   # newline after \r progress
    return results


def str_to_bool(value: str) -> bool:
    return value.strip().lower() in ("true", "1", "yes")


def load_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    start = time.time()

    print("=" * 60)
    print("  SATA — Student Import v2  (optimized)")
    print(f"  CSV  : {CSV_PATH}")
    print("=" * 60)

    # ── 1. Read CSV ────────────────────────────────────────────────────────────
    print("\n[1/5] Reading CSV…")
    rows = load_csv(CSV_PATH)
    print(f"      {len(rows):,} rows loaded.")

    # ── 2. Parallel bcrypt ─────────────────────────────────────────────────────
    print("\n[2/5] Parallel bcrypt hashing…")
    all_ids  = [r["student_id"].strip() for r in rows]
    hash_map = parallel_hash(all_ids)
    print(f"      Done — {len(hash_map):,} hashes generated in {time.time()-start:.1f}s")

    # ── 3. DB work ─────────────────────────────────────────────────────────────
    print("\n[3/5] Connecting to database…")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    cur  = conn.cursor()

    try:
        # Pre-fetch all existing student_ids in one query
        print("[4/5] Fetching existing student IDs…")
        cur.execute("SELECT student_id FROM users WHERE student_id IS NOT NULL")
        existing: set[str] = {row[0] for row in cur.fetchall()}
        print(f"      {len(existing):,} already in DB — will skip duplicates.")

        # ── Build insert tuples ────────────────────────────────────────────────
        print("[5/5] Building insert batches…")
        now = "NOW()"     # resolved server-side

        user_rows:    list[tuple] = []
        profile_rows: list[tuple] = []
        dept_count: dict[str, int] = defaultdict(int)
        skipped = 0

        for raw in rows:
            sid = raw["student_id"].strip()

            if sid in existing:
                skipped += 1
                continue

            uid = uuid.uuid4()
            pid = uuid.uuid4()

            try:
                dept    = raw["department"].strip()
                sem     = int(raw["current_semester"])
                by      = int(raw["batch_year"]) if raw.get("batch_year", "").strip() else None
                perf    = raw.get("performance_status", "").strip() or None
                blogs   = int(raw.get("backlog_count", 0) or 0)
                active  = str_to_bool(raw.get("active_backlog", "False"))
                cgpa    = float(raw["cgpa"]) if raw.get("cgpa", "").strip() else None
            except (ValueError, KeyError) as exc:
                print(f"  [!] Parse error for {sid}: {exc} — skipping")
                skipped += 1
                continue

            user_rows.append((
                str(uid),
                sid,
                raw["email"].strip(),
                hash_map[sid],
                True,       # is_active
                0,          # failed_login_attempts
            ))

            profile_rows.append((
                str(pid),
                str(uid),
                raw["full_name"].strip(),
                dept,
                sem,
                by,
                perf,
                blogs,
                active,
                cgpa,
            ))

            dept_count[dept] += 1
            # Mark as seen so duplicate rows within same CSV don't double-insert
            existing.add(sid)

        inserted = len(user_rows)
        print(f"      {inserted:,} new students to insert, {skipped:,} skipped.")

        # ── Bulk INSERT users ──────────────────────────────────────────────────
        if user_rows:
            print("      → Inserting users…")
            execute_values(
                cur,
                """
                INSERT INTO users
                    (id, student_id, email, password_hash,
                     is_active, failed_login_attempts,
                     created_at, updated_at)
                VALUES %s
                """,
                user_rows,
                template="(%s,%s,%s,%s,%s,%s, NOW(), NOW())",
                page_size=1000,
            )

            # ── Bulk INSERT student_profiles ───────────────────────────────────
            print("      → Inserting student_profiles…")
            execute_values(
                cur,
                """
                INSERT INTO student_profiles
                    (id, user_id, name, department, semester,
                     batch_year, performance_status,
                     backlog_count, active_backlog,
                     cgpa,
                     created_at, updated_at)
                VALUES %s
                """,
                profile_rows,
                template="(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, NOW(), NOW())",
                page_size=1000,
            )

        conn.commit()
        print("      ✓ Committed.")

        # ── Summary ────────────────────────────────────────────────────────────
        elapsed = time.time() - start
        print()
        print("=" * 60)
        print("  IMPORT COMPLETE")
        print("=" * 60)
        print(f"  Total inserted : {inserted:,}")
        print(f"  Total skipped  : {skipped:,}  (duplicates / parse errors)")
        print(f"  Time taken     : {elapsed:.1f}s")
        print()
        print("  Count per department:")
        for dept, count in sorted(dept_count.items(), key=lambda x: -x[1]):
            print(f"    {dept:<30} {count:>6,}")
        print("=" * 60)

    except Exception as exc:
        conn.rollback()
        print(f"\n[!] Unexpected error — rolled back.\n    {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
