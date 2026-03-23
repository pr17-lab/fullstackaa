import pandas as pd
import numpy as np
import random
import csv
from pathlib import Path

random.seed(42)
np.random.seed(42)

# ─────────────────────────────────────────────
# 1. NAME POOLS
# ─────────────────────────────────────────────
FIRST_NAMES = [
    # South Indian
    "Arjun", "Karthik", "Vishnu", "Arun", "Suresh", "Ramesh", "Dinesh", "Ganesh",
    "Vignesh", "Harish", "Praveen", "Sanjay", "Vijay", "Rajesh", "Manoj", "Deepak",
    "Priya", "Divya", "Kavya", "Anjali", "Sneha", "Lakshmi", "Meena", "Revathi",
    "Aishwarya", "Nithya", "Swathi", "Keerthi", "Pooja", "Saranya", "Ananya", "Ramya",
    # North Indian
    "Rohit", "Amit", "Rahul", "Vikram", "Nikhil", "Akash", "Ankit", "Ravi",
    "Gaurav", "Shubham", "Varun", "Aman", "Tarun", "Sachin", "Vivek", "Piyush",
    "Neha", "Pooja", "Shreya", "Rishita", "Aditi", "Riya", "Simran", "Pallavi",
    "Ankita", "Nisha", "Kritika", "Prerna", "Swati", "Mansi", "Sonal", "Tanvi",
    # Muslim names
    "Mohammed", "Faisal", "Irfan", "Asif", "Imran", "Shahid", "Bilal", "Zubair",
    "Syed", "Farhan", "Aamir", "Junaid", "Rizwan", "Salman", "Usman", "Adil",
    "Ayesha", "Fatima", "Zainab", "Sana", "Nadia", "Rukhsar", "Amina", "Hiba",
    # Kerala / Tamil specific
    "Nair", "Menon", "Pillai", "Krishnan", "Rajan", "Babu", "Sathish", "Muralidhar",
    "Sreejith", "Ajith", "Amal", "Jithin", "Athul", "Abhijith", "Avinash", "Harikrishna",
    "Nithish", "Dhanush", "Logesh", "Prithviraj", "Siddharth", "Madhan", "Naveen", "Surya",
]

LAST_NAMES = [
    "Kumar", "Sharma", "Singh", "Verma", "Gupta", "Patel", "Shah", "Mehta",
    "Nair", "Menon", "Pillai", "Krishnan", "Rajan", "Iyer", "Iyengar", "Subramaniam",
    "Reddy", "Rao", "Naidu", "Chetty", "Murthy", "Prasad", "Babu", "Das",
    "Varma", "Joshi", "Mishra", "Pandey", "Tiwari", "Dubey", "Yadav", "Chauhan",
    "Ansari", "Khan", "Siddiqui", "Qureshi", "Sheikh", "Malik", "Mirza", "Hussain",
    "Nambiar", "Warrier", "Namboothiri", "Karunakaran", "Velayudhan", "Gopalakrishnan",
    "Murugan", "Selvam", "Arumugam", "Natarajan", "Chandrasekaran", "Venkataraman",
    "Bhat", "Hegde", "Shetty", "Kamath", "Rao", "Kulkarni", "Patil", "Desai",
]

# ─────────────────────────────────────────────
# 2. DEPARTMENT CONFIG
# ─────────────────────────────────────────────
DEPARTMENTS = {
    "CSE":  {"count": 3000, "cgpa_mean": 7.4, "cgpa_std": 1.0, "backlog_rate": 0.12, "active_backlog_rate": 0.05},
    "ECE":  {"count": 2500, "cgpa_mean": 7.0, "cgpa_std": 1.1, "backlog_rate": 0.20, "active_backlog_rate": 0.10},
    "AIML": {"count": 2000, "cgpa_mean": 7.3, "cgpa_std": 0.9, "backlog_rate": 0.10, "active_backlog_rate": 0.04},
    "MECH": {"count": 2500, "cgpa_mean": 6.6, "cgpa_std": 1.2, "backlog_rate": 0.25, "active_backlog_rate": 0.13},
}

# ─────────────────────────────────────────────
# 3. BATCH → SEMESTER MAPPING (2026 context)
# ─────────────────────────────────────────────
BATCH_CONFIG = [
    {"batch_year": 2022, "current_semester": 8, "count": 2000},
    {"batch_year": 2023, "current_semester": 6, "count": 2500},
    {"batch_year": 2024, "current_semester": 4, "count": 2500},
    {"batch_year": 2025, "current_semester": 2, "count": 2000},
    {"batch_year": 2023, "current_semester": 5, "count": 500},   # repeaters/lateral
    {"batch_year": 2024, "current_semester": 3, "count": 500},   # repeaters/lateral
]

# ─────────────────────────────────────────────
# 4. SUBJECT DEFINITIONS PER DEPT
# ─────────────────────────────────────────────
SUBJECTS = {
    "CSE": {
        1: [("CS101","Engineering Maths I",4,"hard"), ("CS102","Engineering Physics",3,"moderate"),
            ("CS103","C Programming",3,"moderate"), ("CS104","Engineering Drawing",2,"scoring"),
            ("CS105","Environmental Science",2,"scoring")],
        2: [("CS201","Engineering Maths II",4,"hard"), ("CS202","Data Structures",4,"moderate"),
            ("CS203","Digital Electronics",3,"moderate"), ("CS204","Professional Communication",2,"scoring"),
            ("CS205","Constitution of India",2,"scoring")],
        3: [("CS301","DBMS",4,"moderate"), ("CS302","OOP with Java",3,"moderate"),
            ("CS303","Computer Organization",3,"hard"), ("CS304","Discrete Mathematics",4,"hard"),
            ("CS305","Software Engineering",3,"moderate")],
        4: [("CS401","Operating Systems",4,"moderate"), ("CS402","Computer Networks",4,"moderate"),
            ("CS403","Design & Analysis of Algorithms",4,"hard"), ("CS404","Microprocessors",3,"moderate"),
            ("CS405","Web Technologies",3,"scoring")],
        5: [("CS501","Compiler Design",4,"hard"), ("CS502","Artificial Intelligence",3,"moderate"),
            ("CS503","Information Security",3,"moderate"), ("CS504","Cloud Computing",3,"scoring"),
            ("CS505","Professional Ethics",2,"scoring")],
        6: [("CS601","Machine Learning",4,"hard"), ("CS602","Big Data Analytics",3,"moderate"),
            ("CS603","Distributed Systems",3,"moderate"), ("CS604","Mobile Computing",3,"scoring"),
            ("CS605","Elective I",3,"moderate")],
        7: [("CS701","Deep Learning",4,"hard"), ("CS702","DevOps",3,"moderate"),
            ("CS703","Project Management",3,"scoring"), ("CS704","Elective II",3,"moderate"),
            ("CS705","Mini Project",2,"scoring")],
        8: [("CS801","Capstone Project",6,"scoring"), ("CS802","Internship",4,"scoring"),
            ("CS803","Elective III",3,"moderate")],
    },
    "AIML": {
        1: [("AI101","Engineering Maths I",4,"hard"), ("AI102","Statistics & Probability",3,"hard"),
            ("AI103","Python Programming",3,"moderate"), ("AI104","Engineering Drawing",2,"scoring"),
            ("AI105","Environmental Science",2,"scoring")],
        2: [("AI201","Engineering Maths II",4,"hard"), ("AI202","Linear Algebra",4,"hard"),
            ("AI203","Data Structures",3,"moderate"), ("AI204","Professional Communication",2,"scoring"),
            ("AI205","Constitution of India",2,"scoring")],
        3: [("AI301","DBMS",4,"moderate"), ("AI302","OOP with Python",3,"moderate"),
            ("AI303","Probability & Random Processes",4,"hard"), ("AI304","Computer Vision Basics",3,"moderate"),
            ("AI305","Software Engineering",3,"moderate")],
        4: [("AI401","Machine Learning",4,"hard"), ("AI402","Deep Learning Fundamentals",4,"hard"),
            ("AI403","Natural Language Processing",3,"hard"), ("AI404","Big Data Technologies",3,"moderate"),
            ("AI405","Web Technologies",3,"scoring")],
        5: [("AI501","Reinforcement Learning",4,"hard"), ("AI502","Computer Vision",3,"hard"),
            ("AI503","AI Ethics & Fairness",2,"scoring"), ("AI504","Cloud & MLOps",3,"moderate"),
            ("AI505","Professional Ethics",2,"scoring")],
        6: [("AI601","Generative AI",4,"hard"), ("AI602","Time Series Analysis",3,"hard"),
            ("AI603","Recommender Systems",3,"moderate"), ("AI604","Edge AI",3,"moderate"),
            ("AI605","Elective I",3,"moderate")],
        7: [("AI701","Advanced Deep Learning",4,"hard"), ("AI702","AI Product Development",3,"moderate"),
            ("AI703","Research Methodology",3,"scoring"), ("AI704","Elective II",3,"moderate"),
            ("AI705","Mini Project",2,"scoring")],
        8: [("AI801","Capstone Project",6,"scoring"), ("AI802","Internship",4,"scoring"),
            ("AI803","Elective III",3,"moderate")],
    },
    "ECE": {
        1: [("EC101","Engineering Maths I",4,"hard"), ("EC102","Engineering Physics",3,"moderate"),
            ("EC103","Basic Electrical Engg",3,"moderate"), ("EC104","Engineering Drawing",2,"scoring"),
            ("EC105","Environmental Science",2,"scoring")],
        2: [("EC201","Engineering Maths II",4,"hard"), ("EC202","Circuit Theory",4,"hard"),
            ("EC203","Electronic Devices",3,"moderate"), ("EC204","Professional Communication",2,"scoring"),
            ("EC205","Constitution of India",2,"scoring")],
        3: [("EC301","Signals & Systems",4,"hard"), ("EC302","Analog Electronics",3,"moderate"),
            ("EC303","Digital Electronics",3,"moderate"), ("EC304","Electromagnetic Theory",4,"hard"),
            ("EC305","Network Analysis",3,"hard")],
        4: [("EC401","Communication Theory",4,"hard"), ("EC402","Microprocessors & Microcontrollers",4,"moderate"),
            ("EC403","Digital Signal Processing",4,"hard"), ("EC404","Linear Integrated Circuits",3,"moderate"),
            ("EC405","Control Systems",3,"hard")],
        5: [("EC501","VLSI Design",4,"hard"), ("EC502","Digital Communication",3,"moderate"),
            ("EC503","Wireless Communication",3,"moderate"), ("EC504","Embedded Systems",3,"moderate"),
            ("EC505","Professional Ethics",2,"scoring")],
        6: [("EC601","RF & Microwave Engg",4,"hard"), ("EC602","Antenna Theory",3,"hard"),
            ("EC603","Optical Communication",3,"moderate"), ("EC604","IoT & Sensors",3,"scoring"),
            ("EC605","Elective I",3,"moderate")],
        7: [("EC701","5G & Advanced Comm",4,"hard"), ("EC702","Image Processing",3,"moderate"),
            ("EC703","Project Management",3,"scoring"), ("EC704","Elective II",3,"moderate"),
            ("EC705","Mini Project",2,"scoring")],
        8: [("EC801","Capstone Project",6,"scoring"), ("EC802","Internship",4,"scoring"),
            ("EC803","Elective III",3,"moderate")],
    },
    "MECH": {
        1: [("ME101","Engineering Maths I",4,"hard"), ("ME102","Engineering Physics",3,"moderate"),
            ("ME103","Engineering Mechanics",4,"hard"), ("ME104","Engineering Drawing",2,"scoring"),
            ("ME105","Environmental Science",2,"scoring")],
        2: [("ME201","Engineering Maths II",4,"hard"), ("ME202","Thermodynamics",4,"hard"),
            ("ME203","Material Science",3,"moderate"), ("ME204","Professional Communication",2,"scoring"),
            ("ME205","Constitution of India",2,"scoring")],
        3: [("ME301","Fluid Mechanics",4,"hard"), ("ME302","Manufacturing Processes",3,"moderate"),
            ("ME303","Strength of Materials",4,"hard"), ("ME304","Kinematics of Machinery",3,"moderate"),
            ("ME305","Metrology & Measurements",3,"moderate")],
        4: [("ME401","Heat Transfer",4,"hard"), ("ME402","Machine Design I",4,"hard"),
            ("ME403","Dynamics of Machinery",3,"hard"), ("ME404","Applied Thermodynamics",3,"hard"),
            ("ME405","Manufacturing Technology",3,"moderate")],
        5: [("ME501","Machine Design II",4,"hard"), ("ME502","Industrial Engineering",3,"moderate"),
            ("ME503","Finite Element Analysis",3,"hard"), ("ME504","Refrigeration & AC",3,"moderate"),
            ("ME505","Professional Ethics",2,"scoring")],
        6: [("ME601","CAD/CAM",4,"moderate"), ("ME602","Robotics & Automation",3,"moderate"),
            ("ME603","Power Plant Engineering",3,"moderate"), ("ME604","Operations Research",3,"moderate"),
            ("ME605","Elective I",3,"moderate")],
        7: [("ME701","Advanced Manufacturing",4,"moderate"), ("ME702","Product Design",3,"scoring"),
            ("ME703","Project Management",3,"scoring"), ("ME704","Elective II",3,"moderate"),
            ("ME705","Mini Project",2,"scoring")],
        8: [("ME801","Capstone Project",6,"scoring"), ("ME802","Internship",4,"scoring"),
            ("ME803","Elective III",3,"moderate")],
    },
}

# ─────────────────────────────────────────────
# 5. MARKS GENERATION
# ─────────────────────────────────────────────
DIFFICULTY_PARAMS = {
    "hard":     {"cluster1_mean": 58, "cluster1_std": 10, "cluster2_mean": 83, "cluster2_std": 6,  "fail_weight": 0.13, "avg_weight": 0.58, "top_weight": 0.29},
    "moderate": {"cluster1_mean": 66, "cluster1_std": 9,  "cluster2_mean": 85, "cluster2_std": 5,  "fail_weight": 0.06, "avg_weight": 0.58, "top_weight": 0.36},
    "scoring":  {"cluster1_mean": 75, "cluster1_std": 7,  "cluster2_mean": 90, "cluster2_std": 4,  "fail_weight": 0.01, "avg_weight": 0.50, "top_weight": 0.49},
}

def generate_marks(difficulty: str, cgpa_factor: float) -> int:
    """Generate marks for a subject based on difficulty and student's CGPA factor (0-1)."""
    p = DIFFICULTY_PARAMS[difficulty]
    roll = random.random()
    # Adjust thresholds by CGPA factor — stronger students less likely to fail, more likely to top
    fail_w = max(0, p["fail_weight"] * (1.8 - cgpa_factor * 1.6))
    top_w  = min(0.85, p["top_weight"] * (0.3 + cgpa_factor * 1.4))
    avg_w  = max(0.05, 1.0 - fail_w - top_w)

    if roll < fail_w:
        marks = int(np.random.randint(15, 40))
    elif roll < fail_w + avg_w:
        marks = int(np.clip(np.random.normal(p["cluster1_mean"] + (cgpa_factor - 0.5) * 12, p["cluster1_std"]), 40, 79))
    else:
        marks = int(np.clip(np.random.normal(p["cluster2_mean"] + (cgpa_factor - 0.5) * 10, p["cluster2_std"]), 65, 100))
    return int(np.clip(marks, 0, 100))

# ─────────────────────────────────────────────
# 6. BUILD STUDENT LIST
# ─────────────────────────────────────────────
def build_student_pool():
    pool = []
    for batch_cfg in BATCH_CONFIG:
        batch_year = batch_cfg["batch_year"]
        current_sem = batch_cfg["current_semester"]
        total = batch_cfg["count"]
        # Distribute across departments proportionally
        dept_counts = {}
        remaining = total
        dept_list = list(DEPARTMENTS.keys())
        total_dept = sum(DEPARTMENTS[d]["count"] for d in dept_list)
        for i, dept in enumerate(dept_list):
            if i == len(dept_list) - 1:
                dept_counts[dept] = remaining
            else:
                c = round(total * DEPARTMENTS[dept]["count"] / total_dept)
                dept_counts[dept] = c
                remaining -= c
        for dept, cnt in dept_counts.items():
            for _ in range(cnt):
                pool.append({"department": dept, "batch_year": batch_year, "current_semester": current_sem})
    return pool

# ─────────────────────────────────────────────
# 7. MAIN GENERATION
# ─────────────────────────────────────────────
def main():
    output_dir = Path("/mnt/user-data/outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    pool = build_student_pool()
    random.shuffle(pool)
    pool = pool[:10000]

    used_emails = set()
    students = []
    academic_records = []
    record_id = 1

    print("Generating 10,000 students and academic records...")

    for idx, p in enumerate(pool):
        student_id = f"S{idx+1:05d}"
        dept = p["department"]
        batch_year = p["batch_year"]
        current_sem = p["current_semester"]
        dept_cfg = DEPARTMENTS[dept]

        # Name
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        full_name = f"{first} {last}"

        # Email
        base_email = f"{first.lower()}.{last.lower()}"
        attempt = 0
        while True:
            suffix = str(random.randint(10, 99)) if attempt == 0 else str(random.randint(100, 999))
            email = f"{base_email}{suffix}@college.ac.in"
            if email not in used_emails:
                used_emails.add(email)
                break
            attempt += 1

        # Assign student tier based on target distribution: Excellent 8%, Good 38%, Average 38%, At Risk 16%
        tier_roll = random.random()
        if tier_roll < 0.08:
            student_tier = "Excellent"
            cgpa_factor = random.uniform(0.82, 1.0)
        elif tier_roll < 0.46:
            student_tier = "Good"
            cgpa_factor = random.uniform(0.55, 0.82)
        elif tier_roll < 0.84:
            student_tier = "Average"
            cgpa_factor = random.uniform(0.28, 0.55)
        else:
            student_tier = "At Risk"
            cgpa_factor = random.uniform(0.0, 0.28)

        # Apply department skew
        dept_skew = {"CSE": 0.06, "AIML": 0.05, "ECE": 0.0, "MECH": -0.07}
        cgpa_factor = float(np.clip(cgpa_factor + dept_skew.get(dept, 0), 0.0, 1.0))

        # Derive a raw_cgpa estimate from cgpa_factor for backlog logic
        raw_cgpa = 3.0 + cgpa_factor * 7.0

        # Backlogs — probability strongly tied to student tier and CGPA
        # At Risk students MUST have backlogs; low Average very likely to
        if student_tier == "At Risk":
            has_backlog = True
            backlog_prob = 1.0
            active_prob = 0.75
        elif student_tier == "Average" and raw_cgpa < 6.0:
            has_backlog = random.random() < 0.80
            active_prob = 0.55
        elif student_tier == "Average":
            has_backlog = random.random() < 0.30
            active_prob = 0.25
        elif student_tier == "Good":
            has_backlog = random.random() < 0.08
            active_prob = 0.15
        else:  # Excellent
            has_backlog = random.random() < 0.02
            active_prob = 0.05

        # Further scale by department backlog tendency
        dept_backlog_multiplier = dept_cfg["backlog_rate"] / 0.18  # normalize to 1.0 baseline
        if student_tier not in ("At Risk", "Average") or raw_cgpa >= 6.0:
            has_backlog = has_backlog and (random.random() < dept_backlog_multiplier or student_tier == "Average")

        backlog_count = random.randint(1, 5) if has_backlog else 0
        if has_backlog and student_tier == "At Risk":
            backlog_count = random.randint(2, 6)
        active_backlog = has_backlog and (random.random() < active_prob)

        # Performance status from CGPA
        if raw_cgpa >= 8.5:
            perf_status = "Excellent"
        elif raw_cgpa >= 7.0:
            perf_status = "Good"
        elif raw_cgpa >= 5.5:
            perf_status = "Average"
        else:
            perf_status = "At Risk"

        # Generate academic records for each semester up to current
        all_marks = []
        all_credits = []
        for sem in range(1, current_sem + 1):
            subjects = SUBJECTS[dept].get(sem, [])
            for subj_code, subj_name, credits, difficulty in subjects:
                marks = generate_marks(difficulty, cgpa_factor)
                # Force a fail in last semester if active backlog and last sem
                if active_backlog and sem == current_sem and subj_code == subjects[-1][0]:
                    marks = random.randint(18, 38)
                pass_fail = "Pass" if marks >= 40 else "F"
                all_marks.append(marks)
                all_credits.append(credits)
                academic_records.append({
                    "record_id": record_id,
                    "student_id": student_id,
                    "semester": sem,
                    "subject_code": subj_code,
                    "subject_name": subj_name,
                    "credits": credits,
                    "marks_obtained": marks,
                    "total_marks": 100,
                    "pass_fail": pass_fail,
                })
                record_id += 1

        # Recalculate CGPA from actual marks — continuous Anna University style
        if all_marks and all_credits:
            def marks_to_gp(m):
                # Continuous interpolation within slabs — gives realistic decimal CGPA
                if m < 40:  return 0.0
                elif m < 50: return 4.0 + (m - 40) * 0.1   # 4.0–5.0
                elif m < 60: return 5.0 + (m - 50) * 0.1   # 5.0–6.0
                elif m < 70: return 6.0 + (m - 60) * 0.1   # 6.0–7.0
                elif m < 80: return 7.0 + (m - 70) * 0.1   # 7.0–8.0
                elif m < 90: return 8.0 + (m - 80) * 0.1   # 8.0–9.0
                else:        return 9.0 + (m - 90) * 0.1   # 9.0–10.0
            grade_points = [marks_to_gp(m) for m in all_marks]
            total_credits = sum(all_credits)
            weighted_gp = sum(gp * c for gp, c in zip(grade_points, all_credits))
            computed_cgpa = round(weighted_gp / total_credits, 2)
            computed_cgpa = float(np.clip(computed_cgpa, 0.0, 10.0))
        else:
            computed_cgpa = round(raw_cgpa, 2)

        # Recompute performance status from actual CGPA
        if computed_cgpa >= 8.5:
            perf_status = "Excellent"
        elif computed_cgpa >= 7.0:
            perf_status = "Good"
        elif computed_cgpa >= 5.5:
            perf_status = "Average"
        else:
            perf_status = "At Risk"

        students.append({
            "student_id": student_id,
            "full_name": full_name,
            "email": email,
            "department": dept,
            "batch_year": batch_year,
            "current_semester": current_sem,
            "cgpa": computed_cgpa,
            "performance_status": perf_status,
            "backlog_count": backlog_count,
            "active_backlog": active_backlog,
        })

        if (idx + 1) % 1000 == 0:
            print(f"  {idx+1}/10000 students generated...")

    # ─────────────────────────────────────────────
    # POST-GENERATION ENFORCEMENT
    # Ensure logical consistency: low CGPA → must have backlogs
    # ─────────────────────────────────────────────
    for s in students:
        cgpa = s["cgpa"]
        status = s["performance_status"]
        # At Risk (CGPA < 5.5) MUST have backlogs
        if status == "At Risk" and s["backlog_count"] == 0:
            s["backlog_count"] = random.randint(2, 5)
            s["active_backlog"] = True
        # CGPA < 6.0 with no backlog is suspicious — 90% chance to assign one
        elif cgpa < 6.0 and s["backlog_count"] == 0 and random.random() < 0.90:
            s["backlog_count"] = random.randint(1, 3)
            s["active_backlog"] = random.random() < 0.60
        # Excellent students should never have active backlogs
        if status == "Excellent":
            s["backlog_count"] = 0
            s["active_backlog"] = False

    print("✅ Post-generation consistency pass done.")

    # ─────────────────────────────────────────────
    # 8. SAVE TO CSV
    # ─────────────────────────────────────────────
    students_df = pd.DataFrame(students)
    records_df  = pd.DataFrame(academic_records)

    students_path = output_dir / "students.csv"
    records_path  = output_dir / "academic_records.csv"

    students_df.to_csv(students_path, index=False)
    records_df.to_csv(records_path, index=False)

    # ─────────────────────────────────────────────
    # 9. SUMMARY STATS
    # ─────────────────────────────────────────────
    print("\n✅ Generation complete!\n")
    print("=" * 50)
    print(f"📁 students.csv         → {len(students_df):,} rows")
    print(f"📁 academic_records.csv → {len(records_df):,} rows")
    print("=" * 50)

    print("\n🎓 Department Distribution:")
    print(students_df["department"].value_counts().to_string())

    print("\n📅 Batch Year Distribution:")
    print(students_df["batch_year"].value_counts().sort_index().to_string())

    print("\n📊 Semester Distribution:")
    print(students_df["current_semester"].value_counts().sort_index().to_string())

    print("\n📈 Performance Status:")
    print(students_df["performance_status"].value_counts().to_string())

    print(f"\n⭐ Average CGPA: {students_df['cgpa'].mean():.2f}")
    print(f"📉 Min CGPA:     {students_df['cgpa'].min():.2f}")
    print(f"📈 Max CGPA:     {students_df['cgpa'].max():.2f}")

    print("\n📚 Marks Stats:")
    print(f"   Average marks:  {records_df['marks_obtained'].mean():.1f}")
    total_records = len(records_df)
    fails = (records_df["pass_fail"] == "F").sum()
    print(f"   Pass rate:      {((total_records - fails) / total_records * 100):.2f}%")
    print(f"   Total F grades: {fails:,}")

    print("\n🎒 Backlog Stats:")
    print(f"   Students with any backlog:    {students_df['backlog_count'].gt(0).sum():,}")
    print(f"   Students with active backlog: {students_df['active_backlog'].sum():,}")

    print(f"\n📂 Files saved to: {output_dir}")


if __name__ == "__main__":
    main()
