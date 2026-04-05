import json
import os
import sys
import time
import uuid
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

BACKGROUND_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BACKGROUND_DIR / ".env"
load_dotenv(ENV_PATH)
DATABASE_URL = os.getenv("DATABASE_URL")

MISSING_ROLES = [
    "Backend Developer", "Full Stack Developer", "Machine Learning Engineer",
    "Data Analyst", "Cloud Engineer", "QA/Test Engineer", "IoT Engineer",
    "NLP Engineer", "Mobile App Developer"
]

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
    "Embedded Systems Engineer": 28, "Hardware/VLSI Design Engineer": 28,
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
  "MECH": ["Data Scientist", "Data Engineer", "Blockchain Developer", "Frontend Developer"],
  "ECE":  ["Data Scientist", "Data Engineer", "Blockchain Developer", "Frontend Developer"],
  "AIML": ["Hardware/VLSI Design Engineer", "Embedded Systems Engineer", "Blockchain Developer"],
}

WEIGHT_MAP = {"must_have": 3, "preferred": 2, "nice_to_have": 1}

def main():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    cur = conn.cursor()

    cur.execute("SELECT job_role, skill_id::text, importance, min_score_required FROM job_skill_requirements")
    job_role_req = {}
    for role, skill_id, importance, min_req in cur.fetchall():
        if role not in job_role_req: job_role_req[role] = []
        job_role_req[role].append({
            "skill_id": skill_id, "importance": importance, "min_score_required": float(min_req)
        })

    cur.execute("SELECT user_id::text, skill_id::text, confidence_score FROM student_skills")
    student_skills = {}
    for uid, sid, score in cur.fetchall():
        if uid not in student_skills: student_skills[uid] = {}
        student_skills[uid][sid] = float(score)

    cur.execute("SELECT sp.user_id::text, sp.target_roles, pr.department FROM student_preferences sp JOIN student_profiles pr ON pr.user_id = sp.user_id")
    student_info = {}
    for uid, target_roles, dept in cur.fetchall():
        student_info[uid] = {"target_roles": target_roles or [], "dept": dept or ""}

    total_gaps = 0
    all_uids = list(student_info.keys())
    batch_size = 200

    for i in range(0, len(all_uids), batch_size):
        batch = all_uids[i : i + batch_size]
        gaps_inserts = []

        for uid in batch:
            info = student_info[uid]
            dept = info["dept"]
            
            if dept == "AIML":
                targets_to_process = info["target_roles"]
            else:
                targets_to_process = [r for r in info["target_roles"] if r in MISSING_ROLES]
                
            stud_skills = student_skills.get(uid, {})

            for role in targets_to_process:
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
                        if imp == "must_have": sum_weights += w
                        elif imp == "preferred": sum_weights += w * 0.5
                    else:
                        sum_weights += w
                        score = stud_skills[sid]
                        if score >= min_req:
                            sum_met += w
                            strong.append({"skill_id": sid, "score": score})
                        else:
                            weak.append({"skill_id": sid, "score": score, "required": min_req})

                match_score = (sum_met / sum_weights * 100) if sum_weights > 0 else 0.0
                bonus = DEPT_ROLE_BONUS.get(dept, {}).get(role, 0)
                match_score += bonus
                penalties = DEPT_ROLE_PENALTY.get(dept, [])
                if role in penalties: match_score = max(0.0, match_score - 15)
                match_score = max(0.0, min(match_score, 100.0))

                gaps_inserts.append((
                    str(uuid.uuid4()), uid, role, round(match_score, 2),
                    json.dumps(missing), json.dumps(weak), json.dumps(strong)
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
                page_size=500
            )
            conn.commit()
            total_gaps += len(gaps_inserts)

        if (i + len(batch)) % 1000 == 0:
            print(f"  Processed {i + len(batch)} students. Computed {total_gaps} gaps.")

    print(f"Done! Recomputed {total_gaps} gaps.")
    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
