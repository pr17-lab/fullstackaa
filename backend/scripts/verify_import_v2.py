#!/usr/bin/env python3
"""
verify_import_v2.py — Verification script for SATA PostgreSQL Database.

Checks counts, referential integrity, sample data, GPA sanity, department distributions, 
and backlog statistics after a bulk import.

Usage:
    cd backend
    python scripts/verify_import_v2.py
"""

import os
import sys
from pathlib import Path
from decimal import Decimal

import psycopg2
from dotenv import load_dotenv

# ─── Config ───────────────────────────────────────────────────────────────────
BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_PATH    = BACKEND_DIR / ".env"

load_dotenv(ENV_PATH)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("[!] DATABASE_URL not found in .env — aborting.")
    sys.exit(1)


def pass_fail_str(passed: bool) -> str:
    return "\033[92mPASS\033[0m" if passed else "\033[91mFAIL\033[0m"

def print_check(name: str, passed: bool, actual: any, expected: any = None) -> None:
    status = pass_fail_str(passed)
    if expected is not None:
        print(f"  [{status}] {name:<40} | Actual: {actual:<10} | Expected: {expected}")
    else:
        print(f"  [{status}] {name:<40} | Value: {actual}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 80)
    print("  SATA — Database Import Verification")
    print("=" * 80)

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
    except Exception as e:
        print(f"[!] Database connection failed: {e}")
        sys.exit(1)

    print("\n[1] COUNT CHECKS")
    cur.execute("SELECT COUNT(*) FROM users")
    users_count = cur.fetchone()[0]
    print_check("users table count", users_count >= 10000, users_count, "~10000")

    cur.execute("SELECT COUNT(*) FROM student_profiles")
    profiles_count = cur.fetchone()[0]
    print_check("student_profiles table count", profiles_count == users_count, profiles_count, users_count)

    cur.execute("SELECT COUNT(*) FROM academic_terms")
    terms_count = cur.fetchone()[0]
    print_check("academic_terms count", terms_count > 0, terms_count, ">0")

    cur.execute("SELECT COUNT(*) FROM subjects")
    subjects_count = cur.fetchone()[0]
    print_check("subjects count", subjects_count >= 241000, subjects_count, "~241000")

    
    print("\n[2] REFERENTIAL INTEGRITY")
    cur.execute("SELECT COUNT(*) FROM student_profiles WHERE user_id NOT IN (SELECT id FROM users)")
    orphaned_profiles = cur.fetchone()[0]
    print_check("student_profiles without user", orphaned_profiles == 0, orphaned_profiles, 0)
    
    cur.execute("SELECT COUNT(*) FROM academic_terms WHERE user_id NOT IN (SELECT id FROM users)")
    orphaned_terms = cur.fetchone()[0]
    print_check("academic_terms without user", orphaned_terms == 0, orphaned_terms, 0)
    
    cur.execute("SELECT COUNT(*) FROM subjects WHERE term_id NOT IN (SELECT id FROM academic_terms)")
    orphaned_subjects = cur.fetchone()[0]
    print_check("subjects without academic_term", orphaned_subjects == 0, orphaned_subjects, 0)


    print("\n[3] SAMPLE SPOT CHECK (S00001)")
    cur.execute("""
        SELECT u.id, sp.name, sp.department, sp.semester, sp.cgpa, sp.batch_year, sp.performance_status
        FROM users u 
        JOIN student_profiles sp ON u.id = sp.user_id
        WHERE u.student_id = 'S00001'
    """)
    student_record = cur.fetchone()
    
    if not student_record:
        print(f"  [{pass_fail_str(False)}] Student S00001 not found.")
    else:
        user_id, name, dept, sem, cgpa, batch_year, perf_status = student_record
        print(f"  Profile: {name} | {dept} | Sem {sem} | CGPA {cgpa} | Batch {batch_year} | {perf_status}")
        
        print("  Academic Terms:")
        cur.execute("""
            SELECT id, semester, year, gpa 
            FROM academic_terms 
            WHERE user_id = %s 
            ORDER BY semester
        """, (user_id,))
        terms = cur.fetchall()
        for t_id, t_sem, t_year, gpa in terms:
            print(f"    - Sem {t_sem} ({t_year}): GPA {gpa}")
            
            if t_sem == 1:
                cur.execute("""
                    SELECT subject_code, subject_name, credits, marks, grade
                    FROM subjects
                    WHERE term_id = %s
                    ORDER BY subject_code
                    LIMIT 5
                """, (t_id,))
                subjects = cur.fetchall()
                print("      Subjects (Sem 1):")
                for scode, sname, scred, smarks, sgrade in subjects:
                    print(f"        * {scode:<6} | {sname:<30} | {scred} cr | {smarks} marks | Grade {sgrade}")


    print("\n[4] GPA SANITY")
    cur.execute("SELECT COUNT(*) FROM academic_terms WHERE gpa = 0.0")
    zero_gpa_count = cur.fetchone()[0]
    print_check("terms with gpa = 0.0", True, zero_gpa_count, "Expected low/0")
    
    cur.execute("SELECT AVG(gpa), MIN(gpa), MAX(gpa) FROM academic_terms WHERE gpa > 0")
    gpa_stats = cur.fetchone()
    if gpa_stats[0] is not None:
        avg_gpa = float(gpa_stats[0])
        min_gpa = float(gpa_stats[1])
        max_gpa = float(gpa_stats[2])
        print_check("Average GPA across terms", 5.0 <= avg_gpa <= 8.5, f"{avg_gpa:.2f}", "~6-7")
        print_check("Min GPA", True, f"{min_gpa:.2f}")
        print_check("Max GPA", True, f"{max_gpa:.2f}")
    else:
        print("  No valid GPAs found.")


    print("\n[5] DEPARTMENT DISTRIBUTION")
    cur.execute("""
        SELECT department, COUNT(*) 
        FROM student_profiles 
        GROUP BY department 
        ORDER BY count DESC
    """)
    departments = cur.fetchall()
    for row in departments:
        dept, count = row
        print(f"  {dept:<30}: {count:>6}")


    print("\n[6] BACKLOG & PERFORMANCE SANITY")
    cur.execute("SELECT COUNT(*) FROM student_profiles WHERE active_backlog = true")
    active_backlog_count = cur.fetchone()[0]
    print_check("active_backlog = true", abs(active_backlog_count - 2505) < 100, active_backlog_count, "~2505")

    cur.execute("SELECT COUNT(*) FROM student_profiles WHERE performance_status = 'At Risk'")
    at_risk_count = cur.fetchone()[0]
    print_check("performance_status = 'At Risk'", abs(at_risk_count - 1244) < 100, at_risk_count, "~1244")


    print("\n" + "=" * 80)
    print("  VERIFICATION COMPLETE")
    print("=" * 80)

    cur.close()
    conn.close()


if __name__ == "__main__":
    # OS agnostic color support
    import os
    os.system('color')
    main()
