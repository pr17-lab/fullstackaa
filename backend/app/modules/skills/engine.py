import uuid
import json
from sqlalchemy.orm import Session
from app.models.student_profile import StudentProfile
from app.models.student_preference import StudentPreference

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

TOOL_TO_PARENT = {
    "PostgreSQL": "Relational Databases",
    "React": "Web Technology",
    "Docker": "Cloud Computing",
    "FastAPI": "Web Technology",
    "SQL": "Relational Databases",
    "AWS": "Cloud Computing",
    "Kubernetes": "Cloud Computing",
    "OpenCV": "Computer Vision",
    "TensorFlow": "Deep Learning",
    "React Native": "Mobile Computing"
}


def calculate_composite_score(resume: float, project: float, interview: float, communication: float) -> float:
    # Weighted average of non-zero buckets
    w_r = 0.2 if resume > 0 else 0
    w_p = 0.3 if project > 0 else 0
    w_i = 0.3 if interview > 0 else 0
    w_c = 0.2 if communication > 0 else 0
    
    total_w = w_r + w_p + w_i + w_c
    if total_w == 0:
        return 0.0
        
    score = (resume * w_r + project * w_p + interview * w_i + communication * w_c) / total_w
    return float(round(score, 2))

def compute_skills_for_student(db: Session, user_id: str):
    """Computes baseline skills using student's department and interests (cold start)."""
    import uuid
    if isinstance(user_id, str):
        try:
            user_id = uuid.UUID(user_id)
        except ValueError:
            pass
    prof = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
    if not prof:
        return
        
    student_dept = prof.department
    
    # Map department to key taxonomy skills
    dept_skills = {
        "CSE": ["DSA", "DBMS", "Operating Systems", "Computer Networks", "Software Engineering", "OOP", "Python", "Java", "SQL", "PostgreSQL", "React", "Docker", "Git", "CI/CD"],
        "AIML": ["DSA", "DBMS", "OOP", "Python", "SQL", "Machine Learning", "Deep Learning", "NLP", "Computer Vision", "pandas", "scikit-learn", "TensorFlow", "PyTorch", "Data Analysis", "Feature Engineering"],
        "AI&ML": ["DSA", "DBMS", "OOP", "Python", "SQL", "Machine Learning", "Deep Learning", "NLP", "Computer Vision", "pandas", "scikit-learn", "TensorFlow", "PyTorch", "Data Analysis", "Feature Engineering"],
        "ECE": ["C Programming", "C++", "Microcontrollers", "VLSI Design", "Embedded C", "Arduino", "RTOS", "PCB Design", "Circuit Theory", "Signals and Systems", "Digital Electronics", "Analog Electronics", "Communication Systems", "Power Systems"],
        "MECH": ["C Programming", "Python", "Thermodynamics", "Fluid Mechanics", "Strength of Materials", "Manufacturing Processes", "CAD Design", "Heat Transfer"]
    }
    
    skills_to_seed = list(dept_skills.get(student_dept, ["DSA"]))
    
    # Also parse interests
    if prof.interests:
        interests_list = [i.strip().lower() for i in prof.interests.split(",") if i.strip()]
        skill_tax = db.query(SkillTaxonomy).all()
        for s in skill_tax:
            sname = s.skill_name.lower()
            if any(interest in sname or (s.aliases and any(interest in a.lower() for a in s.aliases)) for interest in interests_list):
                if s.skill_name not in skills_to_seed:
                    skills_to_seed.append(s.skill_name)
                    
    skill_tax = db.query(SkillTaxonomy).all()
    skill_name_to_id = {s.skill_name: str(s.id) for s in skill_tax}
    
    for skill_name in skills_to_seed:
        if skill_name not in skill_name_to_id:
            continue
            
        sid = skill_name_to_id[skill_name]
        avg_score = 50.0  # Cold start seed
            
        existing = db.query(StudentSkill).filter(
            StudentSkill.user_id == user_id, 
            StudentSkill.skill_id == sid
        ).first()
        
        if existing:
            existing.resume_weight = avg_score
            
            project_wt = float(existing.project_weight) if existing.project_weight else 0.0
            interview_wt = float(existing.interview_weight) if existing.interview_weight else 0.0
            comm_wt = float(existing.communication_weight) if existing.communication_weight else 0.0
            
            new_confidence = calculate_composite_score(avg_score, project_wt, interview_wt, comm_wt)
            existing.confidence_score = new_confidence
            existing.level = score_to_level(new_confidence)
            
            src_list = list(existing.source) if existing.source else []
            if "resume" not in src_list:
                src_list.append("resume")
                existing.source = src_list
        else:
            new_confidence = calculate_composite_score(avg_score, 0.0, 0.0, 0.0)
            new_skill = StudentSkill(
                id=uuid.uuid4(),
                user_id=user_id,
                skill_id=sid,
                confidence_score=new_confidence,
                level=score_to_level(new_confidence),
                source=["resume"],
                resume_weight=avg_score,
                project_weight=0.0,
                interview_weight=0.0,
                communication_weight=0.0
            )
            db.add(new_skill)
    db.commit()


def compute_gaps_for_student(db: Session, user_id: str):
    from sqlalchemy import text
    import uuid
    if isinstance(user_id, str):
        try:
            user_id = uuid.UUID(user_id)
        except ValueError:
            pass
    
    pref = db.query(StudentPreference).filter(StudentPreference.user_id == user_id).first()
    if not pref:
        return
        
    target_roles = pref.target_roles
    if isinstance(target_roles, str):
        import json
        try:
            target_roles = json.loads(target_roles)
        except Exception:
            pass
    elif isinstance(target_roles, list) and len(target_roles) > 0 and target_roles[0] == '[' and target_roles[-1] == ']':
        import json
        try:
            target_roles = json.loads("".join(target_roles))
        except Exception:
            pass
            
    if not target_roles:
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
    stud_skills = {str(s.skill_id): {
        "score": float(s.confidence_score) if s.confidence_score else 0.0,
        "resume_weight": float(s.resume_weight) if s.resume_weight else 0.0
    } for s in skills}
    
    skill_tax = db.query(SkillTaxonomy).all()
    id_to_name = {str(s.id): s.skill_name for s in skill_tax}
    name_to_id = {s.skill_name: str(s.id) for s in skill_tax}
    
    weight_map = {
        "must_have": 3,
        "preferred": 2,
        "nice_to_have": 1
    }
    
    for role in target_roles:
        if role not in job_reqs:
            continue
            
        reqs = job_reqs[role]
        sum_weights = 0
        sum_met = 0
        missing = []
        weak = []
        strong = []
        high_potential = []
        
        for req in reqs:
            sid = req["skill_id"]
            imp = req["importance"]
            min_req = req["min_score_required"]
            w = weight_map.get(imp, 1)
            
            # Step 1: Look up student's confidence_score for this child skill
            has_child = (sid in stud_skills)
            child_score = stud_skills[sid]["score"] if has_child else 0.0
            
            if has_child and child_score >= 70.0:
                sum_weights += w
                sum_met += w
                strong.append({"skill_id": sid, "score": child_score})
            else:
                # Step 2: Relational query to find tool's parent_id from SkillTaxonomy
                sid_uuid = uuid.UUID(sid) if isinstance(sid, str) else sid
                skill_record = db.query(SkillTaxonomy).filter(SkillTaxonomy.id == sid_uuid).first()
                parent_id = str(skill_record.parent_id) if (skill_record and skill_record.parent_id) else None
                
                has_parent = False
                if parent_id and parent_id in stud_skills:
                    if stud_skills[parent_id]["resume_weight"] > 0:
                        has_parent = True
                        
                if has_parent:
                    sum_weights += w
                    sum_met += w * 0.4  # 40% credit for high potential match
                    high_potential.append({"skill_id": sid, "parent_id": parent_id})
                else:
                    # Step 3: Categorize as weak or missing (0% credit)
                    sum_weights += w
                    if has_child:
                        weak.append({"skill_id": sid, "score": child_score})
                    else:
                        missing.append({"skill_id": sid})
                    
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
            existing.high_potential_skills = high_potential
        else:
            new_gap = SkillGap(
                id=uuid.uuid4(),
                user_id=user_id,
                job_role=role,
                match_score=match_score,
                missing_skills=missing,
                weak_skills=weak,
                strong_skills=strong,
                high_potential_skills=high_potential
            )
            db.add(new_gap)
    db.commit()
