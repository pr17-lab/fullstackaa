import uuid
import json
from sqlalchemy.orm import Session
from app.models.student_profile import StudentProfile
from app.models.student_preference import StudentPreference
from app.models.academic_term import AcademicTerm
from app.models.subject import Subject
from app.models.student_skill import StudentSkill
from app.models.skill_taxonomy import SkillTaxonomy
from app.models.skill_gap import SkillGap
from app.utils.academic import score_to_level

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

def compute_skills_for_student(db: Session, user_id: str):
    """Computes academic skills using user subjects exactly like the V2 script."""
    terms = db.query(AcademicTerm).filter(AcademicTerm.user_id == user_id).all()
    if not terms:
        return
        
    term_ids = [t.id for t in terms]
    subjects = db.query(Subject).filter(Subject.term_id.in_(term_ids)).all()
    
    skill_tax = db.query(SkillTaxonomy).all()
    skill_name_to_id = {s.skill_name: str(s.id) for s in skill_tax}
    
    extracted = {}
    for sub in subjects:
        if sub.marks is None:
            continue
            
        sname = sub.subject_name.strip()
        mapped_skills = []
        if sname in SUBJECT_TO_SKILL:
            mapped_skills = SUBJECT_TO_SKILL[sname]
        else:
            for k, v in SUBJECT_TO_SKILL.items():
                if k.lower() in sname.lower():
                    mapped_skills = v
                    break
                    
        for mapped_skill in mapped_skills:
            if mapped_skill in skill_name_to_id:
                total = float(sub.total_marks) if sub.total_marks else 100.0
                score = (float(sub.marks) / total) * 100
                score = min(score, 100)
                if mapped_skill not in extracted:
                    extracted[mapped_skill] = []
                extracted[mapped_skill].append(score)
                
    for skill_name, scores in extracted.items():
        avg_score = sum(scores) / len(scores)
        sid = skill_name_to_id[skill_name]
        
        level = score_to_level(avg_score)
            
        existing = db.query(StudentSkill).filter(
            StudentSkill.user_id == user_id, 
            StudentSkill.skill_id == sid
        ).first()
        
        if existing:
            existing.confidence_score = avg_score
            existing.level = level
        else:
            new_skill = StudentSkill(
                id=uuid.uuid4(),
                user_id=user_id,
                skill_id=sid,
                confidence_score=avg_score,
                level=level,
                source=["academic"],
                academic_weight=avg_score,
                project_weight=0,
                behavior_weight=0
            )
            db.add(new_skill)
    db.commit()


def compute_gaps_for_student(db: Session, user_id: str):
    from sqlalchemy import text
    
    # Needs a complete raw query mapping job_skill_requirements similar to the DB seeder script computation logic
    pref = db.query(StudentPreference).filter(StudentPreference.user_id == user_id).first()
    if not pref or not pref.target_roles:
        return
        
    prof = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
    student_dept = prof.department if prof else None

    # Load requirements table
    res = db.execute(text("SELECT job_role, skill_id, importance, min_score_required FROM job_skill_requirements"))
    job_reqs = {}
    for row in res.fetchall():
        role = row[0]
        if role not in job_reqs:
            job_reqs[role] = []
        job_reqs[role].append({
            "skill_id": str(row[1]),
            "importance": row[2],
            "min_score_required": float(row[3])
        })
        
    # Load user skills
    skills = db.query(StudentSkill).filter(StudentSkill.user_id == user_id).all()
    stud_skills = {str(s.skill_id): float(s.confidence_score) if s.confidence_score else 0.0 for s in skills}
    
    weight_map = {
        "must_have": 3,
        "preferred": 2,
        "nice_to_have": 1
    }
    
    for role in pref.target_roles:
        if role not in job_reqs:
            continue
            
        reqs = job_reqs[role]
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
                if imp == "preferred":
                    sum_weights += (w * 0.5)
                elif imp == "must_have":
                    sum_weights += w
            else:
                sum_weights += w
                stud_score = stud_skills[sid]
                if stud_score >= min_req:
                    sum_met += w
                    strong.append({"skill_id": sid, "score": stud_score})
                else:
                    weak.append({"skill_id": sid, "score": stud_score, "required": min_req})
                    
        match_score = (sum_met / sum_weights * 100) if sum_weights > 0 else 0
        
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
        
        existing = db.query(SkillGap).filter(SkillGap.user_id == user_id, SkillGap.job_role == role).first()
        if existing:
            existing.match_score = match_score
            existing.missing_skills = missing
            existing.weak_skills = weak
            existing.strong_skills = strong
        else:
            new_gap = SkillGap(
                id=uuid.uuid4(),
                user_id=user_id,
                job_role=role,
                match_score=match_score,
                missing_skills=missing,
                weak_skills=weak,
                strong_skills=strong
            )
            db.add(new_gap)
    db.commit()
