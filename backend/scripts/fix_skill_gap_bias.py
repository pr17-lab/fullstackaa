#!/usr/bin/env python3
"""
fix_skill_gap_bias.py — Fix job recommendation bias in skill_gaps table.

Steps:
  0. Show BEFORE scores per job_role
  1. Update job_skill_requirements: move Git/Docker/CI-CD to nice_to_have
  2. Update Data Engineer specific requirements (MongoDB/Redis -> nice_to_have, ML -> preferred)
  3. Recompute skill_gaps for ALL 10,000 students with improved domain affinity weights
  4. Show AFTER scores per job_role

Usage:
    cd backend
    python scripts/fix_skill_gap_bias.py
"""

import json
import os
import sys
import time
import uuid
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BACKEND_DIR / ".env"

load_dotenv(ENV_PATH)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("[!] DATABASE_URL not found in .env")
    sys.exit(1)


# --- Improved domain affinity weights ----------------------------------------
# Format: {department: {job_role: bonus}}
DEPT_ROLE_BONUS = {
  "CSE": {
    "Software Engineer": 20, "Backend Developer": 22,
    "Full Stack Developer": 20, "Frontend Developer": 15,
    "Data Scientist": 15, "Machine Learning Engineer": 14,
    "Data Engineer": 12, "DevOps Engineer": 12,
    "Cloud Engineer": 12, "Cybersecurity Analyst": 10,
    "Blockchain Developer": 10, "QA/Test Engineer": 10,
    "Data Analyst": 10, "Technical Product Manager": 8,
  },
  "AIML": {
    "Data Scientist": 30, "Machine Learning Engineer": 30,
    "NLP Engineer": 28, "Data Analyst": 20,
    "Data Engineer": 10, "Software Engineer": 10,
    "Backend Developer": 8, "Full Stack Developer": 8,
  },
  "ECE": {
    "Embedded Systems Engineer": 28, 
    "Hardware/VLSI Design Engineer": 28,
    "IoT Engineer": 25, "Cybersecurity Analyst": 15,
    "Cloud Engineer": 10, "Backend Developer": 8,
    "Software Engineer": 8,
  },
  "MECH": {
    "Data Analyst": 15, "IoT Engineer": 20,
    "Embedded Systems Engineer": 18, "Software Engineer": 8,
    "Backend Developer": 8, "QA/Test Engineer": 10,
    "Cloud Engineer": 8,
  }
}

DEPT_ROLE_PENALTY = {
  "MECH": ["Data Scientist", "Data Engineer", 
           "Blockchain Developer", "Frontend Developer"],
  "ECE":  ["Data Scientist", "Data Engineer", 
           "Blockchain Developer", "Frontend Developer"],
  "AIML": ["Hardware/VLSI Design Engineer", 
           "Embedded Systems Engineer",
           "Blockchain Developer"],
}

WEIGHT_MAP = {"must_have": 3, "preferred": 2, "nice_to_have": 1}


def show_scores(cur, label: str):
    cur.execute("""
        SELECT job_role, ROUND(AVG(match_score), 2) as avg, COUNT(*)
        FROM skill_gaps
        GROUP BY job_role
        ORDER BY avg DESC
    """)
    rows = cur.fetchall()
    print(f"\n  -- {label} --")
    print(f"  {'Role':<40} {'Avg Score':>10} {'Count':>8}")
    print(f"  {'-'*40} {'-'*10} {'-'*8}")
    for role, avg, cnt in rows:
        print(f"  {role:<40} {float(avg):>10.2f} {cnt:>8,}")


def main():
    start = time.time()
    print("=" * 70)
    print("  SATA — Fix Skill Gap Bias Script")
    print("=" * 70)

    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    cur = conn.cursor()

    # -- STEP 0: Show BEFORE scores --------------------------------------------
    print("\n[STEP 0] Current average match scores (BEFORE fixes):")
    show_scores(cur, "BEFORE")

    # -- STEP 1: Move Git, Docker, CI/CD etc. to nice_to_have -----------------
    print("\n[STEP 1] Updating tool skills to nice_to_have for CS roles...")
    cur.execute("""
        UPDATE job_skill_requirements 
        SET importance = 'nice_to_have', min_score_required = 40
        WHERE job_role IN ('Software Engineer', 'Data Engineer', 'Frontend Developer')
        AND skill_id IN (
            SELECT id FROM skill_taxonomy 
            WHERE skill_name IN ('Git', 'Docker', 'CI/CD', 'Kubernetes', 'Terraform')
        )
    """)
    rows1 = cur.rowcount
    print(f"  Updated {rows1} requirement rows (Git/Docker/CI-CD -> nice_to_have).")

    # -- STEP 2: Data Engineer specific fixes ----------------------------------
    print("\n[STEP 2] Fixing Data Engineer requirements...")

    # MongoDB, Redis -> nice_to_have
    cur.execute("""
        UPDATE job_skill_requirements
        SET importance = 'nice_to_have', min_score_required = 40
        WHERE job_role = 'Data Engineer'
        AND skill_id IN (
            SELECT id FROM skill_taxonomy WHERE skill_name IN ('MongoDB', 'Redis')
        )
    """)
    rows2a = cur.rowcount
    print(f"  Updated {rows2a} rows (MongoDB/Redis -> nice_to_have for Data Engineer).")

    # Machine Learning -> preferred
    cur.execute("""
        UPDATE job_skill_requirements
        SET importance = 'preferred', min_score_required = 55
        WHERE job_role = 'Data Engineer'
        AND skill_id IN (
            SELECT id FROM skill_taxonomy WHERE skill_name = 'Machine Learning'
        )
    """)
    rows2b = cur.rowcount
    print(f"  Updated {rows2b} rows (Machine Learning -> preferred for Data Engineer).")

    conn.commit()
    print("  Changes committed.")

    # -- STEP 3: Load fresh job_skill_requirements from DB ---------------------
    print("\n[STEP 3] Reloading job requirements from DB...")
    cur.execute("""
        SELECT job_role, skill_id::text, importance, min_score_required
        FROM job_skill_requirements
    """)
    job_role_req: dict[str, list] = {}
    for role, skill_id, importance, min_req in cur.fetchall():
        if role not in job_role_req:
            job_role_req[role] = []
        job_role_req[role].append({
            "skill_id": skill_id,
            "importance": importance,
            "min_score_required": float(min_req),
        })
    print(f"  Loaded requirements for {len(job_role_req)} roles.")

    # -- STEP 3b: Load student skills ------------------------------------------
    print("\n[STEP 3b] Loading student skills...")
    cur.execute("""
        SELECT user_id::text, skill_id::text, confidence_score
        FROM student_skills
    """)
    student_skills: dict[str, dict[str, float]] = {}
    for uid, sid, score in cur.fetchall():
        if uid not in student_skills:
            student_skills[uid] = {}
        student_skills[uid][sid] = float(score)
    print(f"  Loaded skills for {len(student_skills):,} students.")

    # -- STEP 3c: Load student preferences ------------------------------------
    print("\n[STEP 3c] Loading student preferences and departments...")
    cur.execute("""
        SELECT sp.user_id::text, sp.target_roles, pr.department
        FROM student_preferences sp
        JOIN student_profiles pr ON pr.user_id = sp.user_id
    """)
    student_info: dict[str, dict] = {}
    for uid, target_roles, dept in cur.fetchall():
        student_info[uid] = {
            "target_roles": target_roles or [],
            "dept": dept or "",
        }
    print(f"  Loaded preferences for {len(student_info):,} students.")

    # -- STEP 4: Recompute skill_gaps with improved model ---------------------
    print("\n[STEP 4] Recomputing skill gaps for all students...")
    total_gaps = 0
    batch_size = 500
    all_uids = list(student_info.keys())

    for i in range(0, len(all_uids), batch_size):
        batch = all_uids[i : i + batch_size]
        gaps_inserts = []

        for uid in batch:
            info = student_info[uid]
            targets = info["target_roles"]
            dept = info["dept"]
            stud_skills = student_skills.get(uid, {})

            for role in targets:
                if role not in job_role_req:
                    continue

                reqs = job_role_req[role]
                sum_weights = 0.0
                sum_met = 0.0
                missing, weak, strong = [], [], []

                for req in reqs:
                    sid = req["skill_id"]
                    imp = req["importance"]
                    min_req = req["min_score_required"]
                    w = WEIGHT_MAP.get(imp, 1)

                    if sid not in stud_skills:
                        missing.append({"skill_id": sid, "importance": imp, "gap": True})
                        if imp == "must_have":
                            sum_weights += w   # full penalty
                        elif imp == "preferred":
                            sum_weights += w * 0.5  # half penalty
                        # nice_to_have -> no penalty (neutral)
                    else:
                        sum_weights += w
                        score = stud_skills[sid]
                        if score >= min_req:
                            sum_met += w
                            strong.append({"skill_id": sid, "score": score})
                        else:
                            weak.append({"skill_id": sid, "score": score, "required": min_req})

                match_score = (sum_met / sum_weights * 100) if sum_weights > 0 else 0.0

                # Department-based affinity bonus
                dept_bonuses = DEPT_ROLE_BONUS.get(dept, {})
                bonus = dept_bonuses.get(role, 0)
                match_score += bonus

                # Department-based penalty
                penalties = DEPT_ROLE_PENALTY.get(dept, [])
                if role in penalties:
                    match_score = max(0.0, match_score - 15)

                match_score = max(0.0, min(match_score, 100.0))

                gaps_inserts.append((
                    str(uuid.uuid4()),
                    uid,
                    role,
                    round(match_score, 2),
                    json.dumps(missing),
                    json.dumps(weak),
                    json.dumps(strong),
                ))

        if gaps_inserts:
            execute_values(
                cur,
                """
                INSERT INTO skill_gaps 
                (id, user_id, job_role, match_score, missing_skills, weak_skills, strong_skills, computed_at)
                VALUES %s
                ON CONFLICT (user_id, job_role) DO UPDATE SET
                    match_score     = EXCLUDED.match_score,
                    missing_skills  = EXCLUDED.missing_skills,
                    weak_skills     = EXCLUDED.weak_skills,
                    strong_skills   = EXCLUDED.strong_skills,
                    computed_at     = now()
                """,
                gaps_inserts,
                template="(%s::uuid, %s::uuid, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, now())",
                page_size=500,
            )
            conn.commit()
            total_gaps += len(gaps_inserts)

        pct = min((i + len(batch)) / len(all_uids) * 100, 100)
        print(f"  Progress: {i + len(batch):>6,}/{len(all_uids):,}  ({pct:.0f}%)  gaps={total_gaps:,}", flush=True)

    print(f"\n  Done. Recomputed {total_gaps:,} skill gap records.")

    # -- STEP 5: Show AFTER scores ---------------------------------------------
    print("\n[STEP 5] Updated average match scores (AFTER fixes):")
    show_scores(cur, "AFTER")

    elapsed = time.time() - start
    print(f"\n  Total time: {elapsed:.1f}s")
    print("=" * 70)

    cur.close()
    conn.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print(f"\n[!] Error: {e}")
        traceback.print_exc()
        sys.exit(1)
