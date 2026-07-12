#!/usr/bin/env python3
"""
seed_v2_pipeline.py — V2 Career Intelligence Orchestration Script

Steps:
1. Import skill_taxonomy.csv
2. Import job_skill_requirements.csv
3. Seed student_preferences for all students based on department logic
4. Run skill extraction (subject mapping) for all students
5. Compute skill gaps for all students against preferred roles
6. Backfill behavior_summary from existing interview_sessions
"""

import csv
import json
import os
import random
import sys
import time
from pathlib import Path
from uuid import UUID

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

BACKGROUND_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BACKGROUND_DIR / ".env"
DATA_DIR = BACKGROUND_DIR / "data"

load_dotenv(ENV_PATH)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("[!] DATABASE_URL not found in .env — aborting.")
    sys.exit(1)


# STEP 4 Mapping dict
SUBJECT_TO_SKILL = {
  "Data Structures": ["DSA"],
  "Design and Analysis of Algorithms": ["DSA"], 
  "Database Management Systems": ["DBMS", "SQL", "PostgreSQL"],
  "DBMS": ["DBMS", "SQL", "PostgreSQL"],
  "Operating Systems": ["Operating Systems"],
  "Computer Networks": ["Computer Networks"],
  "Software Engineering": ["Software Engineering", "Git", "CI/CD"],
  "Object Oriented Programming": ["OOP"],
  "OOP with Java": ["OOP", "Java"],
  "OOP with Python": ["OOP", "Python"],
  "Python Programming": ["Python"],
  "Java Programming": ["Java"],
  "Web Technology": ["HTML", "JavaScript", "REST APIs", "CSS", "React"],
  "Web Technologies": ["HTML", "JavaScript", "REST APIs", "CSS", "React"],
  "Internet of Things": ["Microcontrollers"],
  "IoT & Sensors": ["Microcontrollers"],
  "Machine Learning": ["Machine Learning", "Python"],
  "Deep Learning": ["Deep Learning", "TensorFlow"],
  "Natural Language Processing": ["NLP"],
  "Computer Vision": ["Computer Vision", "OpenCV"],
  "Thermodynamics": ["Thermodynamics"],
  "Applied Thermodynamics": ["Thermodynamics"],
  "Fluid Mechanics": ["Fluid Mechanics"],
  "Strength of Materials": ["Strength of Materials"],
  "Manufacturing Processes": ["Manufacturing Processes"],
  "Circuit Theory": ["Circuit Theory"],
  "Signals and Systems": ["Signals and Systems"],
  "Signals & Systems": ["Signals and Systems"],
  "Digital Electronics": ["Digital Electronics"],
  "Analog Electronics": ["Analog Electronics"],
  "VLSI Design": ["VLSI Design"],
  "Embedded Systems": ["Embedded C", "Microcontrollers"],
  "Microprocessors and Microcontrollers": ["Microcontrollers", "Embedded C"],
  "Communication Systems": ["Communication Systems"],
  "Fundamentals of Programming": ["Python"],
  "Problem Solving and Python": ["Python"],  
  "Programming in Python": ["Python"],
  "C Programming": ["C"],
  "Data Science Fundamentals": ["Python", "Data Analysis"],
  "Artificial Intelligence": ["Machine Learning"],
  "Statistical Methods": ["Machine Learning"],
  "Big Data Analytics": ["Data Analysis", "Python", "SQL"],
  "Cloud Computing": ["AWS", "Docker"],
  "Cloud & MLOps": ["AWS", "Docker", "Kubernetes", "CI/CD"],
  "Cyber Security": ["Computer Networks", "Cybersecurity"],
  "DevOps": ["Git", "Docker", "CI/CD", "Kubernetes", "AWS"],
  "Mobile Application Development": ["JavaScript", "React Native"],
  "Mobile Computing": ["JavaScript", "React Native"],
}


def main():
    start_time = time.time()
    print("=" * 70)
    print("  SATA — V2 Career Intelligence Seed Pipeline")
    print("=" * 70)

    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        cur = conn.cursor()
    except Exception as e:
        print(f"[!] Database Connection Failed: {e}")
        sys.exit(1)

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 1: Import skill_taxonomy
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[STEP 1] Importing skill_taxonomy.csv...")
    try:
        csv_path = DATA_DIR / "skill_taxonomy.csv"
        skill_name_to_id = {}
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data = []
            for row in reader:
                # Need to convert string of aliases like "A|B|C" back to PostgreSQL array
                aliases_raw = row['aliases'].strip()
                aliases = aliases_raw.split('|') if aliases_raw else []
                # (id, skill_name, category, aliases, description)
                data.append((
                    row['id'], 
                    row['skill_name'], 
                    row['category'], 
                    aliases, 
                    row['description'],
                    'concept'
                ))
                skill_name_to_id[row['skill_name']] = row['id']
                
        execute_values(
            cur,
            """
            INSERT INTO skill_taxonomy (id, skill_name, category, aliases, description, skill_type)
            VALUES %s
            ON CONFLICT (skill_name) DO NOTHING
            """,
            data,
            template="(%s::uuid, %s, %s, %s::text[], %s, %s)"
        )
        conn.commit()
        inserted_skills = cur.rowcount
        print(f"  - Processed {len(data)} skills from CSV. Inserted: {inserted_skills}, Skipped duplicates: {len(data) - inserted_skills}")
    except Exception as e:
        conn.rollback()
        print(f"  [!] Step 1 Failed: {e}")
        sys.exit(1)


    # ──────────────────────────────────────────────────────────────────────────
    # STEP 2: Import job_skill_requirements
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[STEP 2] Importing job_skill_requirements.csv...")
    try:
        csv_path = DATA_DIR / "job_skill_requirements.csv"
        job_counts = {}
        data = []
        
        job_role_requirements_cache = {} # Used later for gaps

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                role = row['job_role']
                data.append((
                    row['id'],
                    role,
                    row['skill_id'],
                    row['importance'],
                    float(row['min_score_required']),
                    row.get('last_reviewed_at') or '2026-03-01 00:00:00+00:00'
                ))
                
                # Caching for Step 5
                if role not in job_role_requirements_cache:
                    job_role_requirements_cache[role] = []
                job_role_requirements_cache[role].append({
                    "skill_id": row['skill_id'],
                    "importance": row['importance'],
                    "min_score_required": float(row['min_score_required'])
                })

        execute_values(
            cur,
            """
            INSERT INTO job_skill_requirements (id, job_role, skill_id, importance, min_score_required, last_reviewed_at)
            VALUES %s
            ON CONFLICT (job_role, skill_id) DO UPDATE SET last_reviewed_at = EXCLUDED.last_reviewed_at
            """,
            data,
            template="(%s::uuid, %s, %s::uuid, %s, %s, %s::timestamptz)"
        )
        conn.commit()
        
        # Manually track job roles inserted/processed
        for d in data:
            job_counts[d[1]] = job_counts.get(d[1], 0) + 1
            
        print(f"  - Processed {len(data)} job skill requirements.")
        for k, v in job_counts.items():
            print(f"    - {k}: {v} skills")
        print("\n[INFO] Exiting seed pipeline early after Step 2.")
        sys.exit(0)
    except Exception as e:
        conn.rollback()
        print(f"  [!] Step 2 Failed: {e}")
        sys.exit(1)


    # ──────────────────────────────────────────────────────────────────────────
    # STEP 3: Seed student_preferences
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[STEP 3] Seeding student_preferences for all users...")
    try:
        cur.execute("SELECT user_id, department FROM student_profiles")
        users_depts = cur.fetchall()
        
        prefs_data = []
        dept_counts = {}
        
        student_target_roles_cache = {} # Needed for Step 5
        student_dept_cache = {} # Needed for Step 5 domain bonus
        
        # To avoid duplicate ids issue when ON CONFLICT DO NOTHING, auto-generate standard uuids
        for uid, dept in users_depts:
            import uuid
            pid = str(uuid.uuid4())
            target_roles = []
            pref_doms = []
            c_trans = False
            t_from = None
            t_to = None
            
            # Logic based on department
            if dept in ("CSE", "AIML", "AI&ML"):
                target_roles = ["Software Engineer", "Data Scientist", "Data Engineer"]
                pref_doms = ["Software", "AI/ML"]
                c_trans = False
            elif dept == "ECE":
                if random.random() < 0.6:
                    target_roles = ["Embedded Systems Engineer", "Hardware/VLSI Design Engineer"]
                    pref_doms = ["Hardware", "Embedded systems"]
                    c_trans = False
                else:
                    target_roles = ["Software Engineer", "Data Scientist"]
                    pref_doms = ["Software", "AI/ML"]
                    c_trans = True
                    t_from = "Electronics"
                    t_to = "Software Engineering"
            elif dept == "MECH":
                rand_val = random.random()
                if rand_val < 0.4:
                    target_roles = ["Software Engineer", "Data Analyst"]
                    pref_doms = ["Software", "Data"]
                    c_trans = True
                    t_from = "Mechanical"
                    t_to = "Software/Data"
                elif rand_val < 0.7:
                    target_roles = ["Mechanical Design Engineer", "Robotics/Mechatronics Engineer"]
                    pref_doms = ["Mechanical", "Embedded systems"]
                    c_trans = False
                else:
                    target_roles = ["Automotive Engineer", "Manufacturing Engineer"]
                    pref_doms = ["Automotive", "Manufacturing"]
                    c_trans = False
            else:
                target_roles = ["Software Engineer"]
                pref_doms = ["Software"]
                
            timeline = random.randint(3, 12)
            exp_lvl = "fresher"
            open_rem = (random.random() < 0.8)
            
            student_target_roles_cache[uid] = target_roles
            student_dept_cache[uid] = dept
            dept_counts[dept] = dept_counts.get(dept, 0) + 1
            
            # (id, user_id, target_roles, preferred_domains, open_to_remote, career_transition, 
            #  transition_from, transition_to, timeline_months, experience_level)
            prefs_data.append((
                pid, uid, target_roles, pref_doms, open_rem, c_trans,
                t_from, t_to, timeline, exp_lvl
            ))
            
        execute_values(
            cur,
            """
            INSERT INTO student_preferences 
            (id, user_id, target_roles, preferred_domains, open_to_remote, career_transition,
             transition_from, transition_to, timeline_months, experience_level)
            VALUES %s
            ON CONFLICT (user_id) DO NOTHING
            """,
            prefs_data,
            template="(%s::uuid, %s::uuid, %s::text[], %s::text[], %s::boolean, %s::boolean, %s, %s, %s::int, %s)",
            page_size=1000
        )
        conn.commit()
        print(f"  - Processed preferences for {len(prefs_data)} students.")
        for k, v in dept_counts.items():
            print(f"    - {k}: {v}")
    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
        print(f"  [!] Step 3 Failed: {e}")
        sys.exit(1)


    # ──────────────────────────────────────────────────────────────────────────
    # STEP 4: Run skill extraction mapping
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[STEP 4] Running skill extraction for all students...")
    total_skills_inserted = 0
    try:
        # Load skill_taxonomy cache if empty
        if not skill_name_to_id:
            cur.execute("SELECT skill_name, id FROM skill_taxonomy")
            for sr in cur.fetchall():
                skill_name_to_id[sr[0]] = sr[1]

        # Fetch all academic terms & subjects, group by user explicitly via pure SQL
        # This prevents 10,000 separate DB subqueries
        print("  Extracting bulk subject marks...")
        cur.execute("""
            SELECT at.user_id, s.subject_name, s.marks, s.total_marks
            FROM academic_terms at
            JOIN subjects s ON s.term_id = at.id
        """)
        user_subjects = {}
        for row in cur.fetchall():
            uid = row[0]
            if uid not in user_subjects:
                user_subjects[uid] = []
            user_subjects[uid].append({
                "name": row[1],
                "marks_obtained": float(row[2]) if row[2] else 0,
                "total_marks": float(row[3]) if row[3] else 100
            })

        print(f"  Fetched records for {len(user_subjects)} users. Computing batch extractions...")

        all_uids = list(user_subjects.keys())
        batch_size = 200
        student_skills_cache = {} # Important for Step 5!
        
        import uuid
        
        for i in range(0, len(all_uids), batch_size):
            batch_uids = all_uids[i:i+batch_size]
            batch_skill_inserts = []
            
            for uid in batch_uids:
                subs = user_subjects[uid]
                
                # dict of skill_name -> [scores...]
                extracted = {}
                for sub in subs:
                    sname = sub["name"].strip()
                    # Fuzzy map via dict
                    mapped_skills = []
                    if sname in SUBJECT_TO_SKILL:
                        mapped_skills = SUBJECT_TO_SKILL[sname]
                    else:
                        # Attempt generic fallback mapping if exact string matches
                        for k, v in SUBJECT_TO_SKILL.items():
                            if k.lower() in sname.lower():
                                mapped_skills = v
                                break
                                
                    if mapped_skills:
                        for mapped_skill in mapped_skills:
                            if mapped_skill in skill_name_to_id:
                                total = sub["total_marks"] if sub["total_marks"] > 0 else 100
                                score = (sub["marks_obtained"] / total) * 100
                                score = min(score, 100) # cap
                                
                                if mapped_skill not in extracted:
                                    extracted[mapped_skill] = []
                                extracted[mapped_skill].append(score)
                
                # compute averages
                student_skills_cache[uid] = {}
                
                for skill_name, scores in extracted.items():
                    avg_score = sum(scores) / len(scores)
                    sid = skill_name_to_id[skill_name]
                    
                    if avg_score >= 70:
                        level = "strong"
                    elif avg_score >= 45:
                        level = "moderate"
                    else:
                        level = "weak"
                        
                    # cache for step 5
                    student_skills_cache[uid][sid] = avg_score
                        
                    batch_skill_inserts.append((
                        str(uuid.uuid4()),
                        uid,
                        sid,
                        avg_score,
                        level,
                        ["academic"],
                        avg_score,
                        0,
                        0
                    ))

            if batch_skill_inserts:
                execute_values(
                    cur,
                    """
                    INSERT INTO student_skills 
                    (id, user_id, skill_id, confidence_score, level, source, 
                     academic_weight, project_weight, behavior_weight, last_computed_at)
                    VALUES %s
                    ON CONFLICT (user_id, skill_id) DO UPDATE SET
                    confidence_score = EXCLUDED.confidence_score,
                    level = EXCLUDED.level,
                    last_computed_at = now()
                    """,
                    batch_skill_inserts,
                    template="(%s::uuid, %s::uuid, %s::uuid, %s, %s, %s::text[], %s, %s, %s, now())",
                    page_size=500
                )
                total_skills_inserted += len(batch_skill_inserts)
                conn.commit()
                
            if (i + batch_size) % 1000 == 0:
                print(f"    ... processed {i + len(batch_uids)} students")

        print(f"  - Processed Step 4. Generated {total_skills_inserted} student_skills records.")
    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
        print(f"  [!] Step 4 Failed: {e}")
        sys.exit(1)


    # ──────────────────────────────────────────────────────────────────────────
    # STEP 5: Compute skill gaps
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[STEP 5] Computing skill gaps from preferences...")
    total_gaps_created = 0
    try:
        import uuid
        
        all_uids_gaps = list(student_target_roles_cache.keys())
        batch_size = 200
        
        weight_map = {
            "must_have": 3,
            "preferred": 2,
            "nice_to_have": 1
        }
        
        for i in range(0, len(all_uids_gaps), batch_size):
            batch_uids = all_uids_gaps[i:i+batch_size]
            gaps_inserts = []
            
            for uid in batch_uids:
                targets = student_target_roles_cache.get(uid, [])
                stud_skills = student_skills_cache.get(uid, {})
                
                for role in targets:
                    if role not in job_role_requirements_cache:
                        continue
                    
                    reqs = job_role_requirements_cache[role]
                    sum_weights = 0
                    sum_met = 0
                    
                    missing = []
                    weak = []
                    strong = []
                    
                    for req in reqs:
                        sid = req["skill_id"]
                        imp = req["importance"]
                        min_req = req["min_score_required"]
                        w = weight_map.get(imp, 1)
                        
                        if sid not in stud_skills:
                            missing.append({"skill_id": sid, "importance": imp, "gap": True})
                            if imp == "nice_to_have":
                                pass # Neutral, no penalty
                            elif imp == "preferred":
                                sum_weights += (w * 0.5) # Half penalty
                            else:
                                sum_weights += w # Full penalty for must_have
                        else:
                            sum_weights += w
                            stud_score = stud_skills[sid]
                            if stud_score >= min_req:
                                sum_met += w
                                strong.append({"skill_id": sid, "score": stud_score})
                            else:
                                weak.append({"skill_id": sid, "score": stud_score, "required": min_req})
                                
                    # Match score
                    match_score = (sum_met / sum_weights * 100) if sum_weights > 0 else 0
                    
                    # DOMAIN BONUS
                    student_dept = student_dept_cache.get(uid)
                    dept_bonus = [
                        "Software Engineer", "Data Scientist", "Data Engineer",
                        "Frontend Developer", "DevOps Engineer", "Cybersecurity Analyst",
                        "Blockchain Developer", "Technical Product Manager"
                    ]
                    ece_bonus = [
                        "Embedded Systems Engineer", "Hardware/VLSI Design Engineer",
                        "Cybersecurity Analyst"
                    ]
                    mech_bonus = [
                        "Mechanical Design Engineer", "Manufacturing Engineer", "Automotive Engineer",
                        "HVAC Engineer", "Robotics/Mechatronics Engineer"
                    ]
                    if student_dept in ("CSE", "AIML", "AI&ML") and role in dept_bonus:
                        match_score += 15
                    elif student_dept == "ECE" and role in ece_bonus:
                        match_score += 15
                    elif student_dept == "MECH" and role in mech_bonus:
                        match_score += 15
                        
                    match_score = min(match_score, 100.0)
                    
                    gaps_inserts.append((
                        str(uuid.uuid4()),
                        uid,
                        role,
                        match_score,
                        json.dumps(missing),
                        json.dumps(weak),
                        json.dumps(strong)
                    ))
                    
            if gaps_inserts:
                execute_values(
                    cur,
                    """
                    INSERT INTO skill_gaps 
                    (id, user_id, job_role, match_score, missing_skills, weak_skills, strong_skills, computed_at)
                    VALUES %s
                    ON CONFLICT (user_id, job_role) DO UPDATE SET
                    match_score = EXCLUDED.match_score,
                    missing_skills = EXCLUDED.missing_skills,
                    weak_skills = EXCLUDED.weak_skills,
                    strong_skills = EXCLUDED.strong_skills,
                    computed_at = EXCLUDED.computed_at
                    """,
                    gaps_inserts,
                    template="(%s::uuid, %s::uuid, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, now())",
                    page_size=500
                )
                conn.commit()
                total_gaps_created += len(gaps_inserts)
                
            if (i + len(batch_uids)) % 1000 == 0:
                print(f"    ... gaps computed for {i + len(batch_uids)} students")
                
        print(f"  - Processed Step 5. Generated {total_gaps_created} skill_gaps records.")
    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
        print(f"  [!] Step 5 Failed: {e}")
        sys.exit(1)


    # ──────────────────────────────────────────────────────────────────────────
    # STEP 6: Backfill behavior_summary
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[STEP 6] Computing macro behavior summaries...")
    try:
        cur.execute("""
            WITH interview_stats AS (
                SELECT 
                    iss.user_id,
                    COUNT(CASE WHEN iss.status = 'completed' THEN 1 END) as completed_count,
                    COUNT(CASE WHEN iss.status = 'abandoned' THEN 1 END) as abandoned_count,
                    MAX(iss.created_at) as last_active_at
                FROM interview_sessions iss
                GROUP BY iss.user_id
            ),
            question_stats AS (
                SELECT 
                    iss.user_id,
                    COUNT(iq.id) as q_answered
                FROM interview_sessions iss
                JOIN interview_questions iq ON iq.session_id = iss.id
                WHERE iq.user_answer IS NOT NULL AND iq.user_answer != ''
                GROUP BY iss.user_id
            ),
            all_users AS (
                SELECT id as user_id FROM users
            )
            SELECT 
                u.user_id,
                COALESCE(i.completed_count, 0) as interviews_completed,
                COALESCE(i.abandoned_count, 0) as interviews_abandoned,
                COALESCE(q.q_answered, 0) as questions_answered,
                0 as roadmap_tasks_done,
                i.last_active_at
            FROM all_users u
            LEFT JOIN interview_stats i ON i.user_id = u.user_id
            LEFT JOIN question_stats q ON q.user_id = u.user_id
        """)
        
        behavior_inserts = []
        import uuid
        
        for row in cur.fetchall():
            uid = row[0]
            compl = row[1]
            aband = row[2]
            q_ans = row[3]
            rt_done = row[4]
            last_act = row[5]
            
            cons_score = min(compl * 10 + q_ans * 2, 100)
            if cons_score >= 70:
                eng = "high"
            elif cons_score >= 40:
                eng = "medium"
            else:
                eng = "low"
                
            behavior_inserts.append((
                str(uuid.uuid4()),
                uid,
                compl,
                aband,
                q_ans,
                rt_done,
                last_act,
                cons_score,
                eng
            ))
            
        execute_values(
            cur,
            """
            INSERT INTO behavior_summary
            (id, user_id, interviews_completed, interviews_abandoned, questions_answered,
             roadmap_tasks_done, last_active_at, consistency_score, engagement_level)
            VALUES %s
            ON CONFLICT (user_id) DO UPDATE SET
            interviews_completed = EXCLUDED.interviews_completed,
            interviews_abandoned = EXCLUDED.interviews_abandoned,
            questions_answered = EXCLUDED.questions_answered,
            consistency_score = EXCLUDED.consistency_score,
            engagement_level = EXCLUDED.engagement_level,
            last_active_at = EXCLUDED.last_active_at
            """,
            behavior_inserts,
            template="(%s::uuid, %s::uuid, %s, %s, %s, %s, %s, %s, %s)",
            page_size=1000
        )
        conn.commit()
        print(f"  - Processed Step 6. Generated bulk behavior_summary for {len(behavior_inserts)} users.")

    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
        print(f"  [!] Step 6 Failed: {e}")
        sys.exit(1)


    # ──────────────────────────────────────────────────────────────────────────
    # POST-RUN DIAGNOSTICS
    # ──────────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  SEED PIPELINE COMPLETE STATS")
    print("=" * 70)
    
    cur.execute("SELECT COUNT(DISTINCT user_id) FROM student_skills")
    students_with_skills = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM skill_gaps")
    total_gaps = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM behavior_summary")
    total_behave = cur.fetchone()[0]
    
    cur.execute("SELECT ROUND(AVG(match_score), 2) FROM skill_gaps")
    avg_gap_score = cur.fetchone()[0] or 0

    print(f"  Total students with skills computed : {students_with_skills:,}")
    print(f"  Total skill_gap records created     : {total_gaps:,}")
    print(f"  Total behavior_summary records      : {total_behave:,}")
    print(f"  Average Match Score (all gaps)      : {avg_gap_score}%")
    print(f"  Total Runtime                       : {time.time() - start_time:.1f}s")
    print("=" * 70)

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
