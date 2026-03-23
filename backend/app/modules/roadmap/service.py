from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
import uuid
from typing import List
from fastapi import HTTPException

from app.models.roadmap import Roadmap, RoadmapTask
from app.models.skill_taxonomy import SkillTaxonomy
from app.models.skill_gap import SkillGap
from app.models.student_preference import StudentPreference
from .schemas import RoadmapSummary, RoadmapResponse, RoadmapTaskResponse

def get_roadmaps(db: Session, user_id: UUID) -> List[RoadmapSummary]:
    roadmaps = db.query(Roadmap).filter(Roadmap.user_id == user_id).order_by(Roadmap.created_at.desc()).all()
    results = []
    for r in roadmaps:
        tot = r.total_tasks if r.total_tasks else 1
        comp = r.completed_tasks if r.completed_tasks else 0
        pct = (comp / tot * 100) if tot > 0 else 0.0
        results.append(RoadmapSummary(
            id=r.id,
            job_role=r.job_role,
            version=r.version,
            status=r.status,
            completion_percentage=pct,
            created_at=r.created_at
        ))
    return results

def get_roadmap(db: Session, user_id: UUID, roadmap_id: UUID) -> RoadmapResponse:
    r = db.query(Roadmap).filter(Roadmap.id == roadmap_id, Roadmap.user_id == user_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Roadmap not found")
        
    tasks_query = (
        db.query(RoadmapTask, SkillTaxonomy.skill_name)
        .outerjoin(SkillTaxonomy, RoadmapTask.skill_id == SkillTaxonomy.id)
        .filter(RoadmapTask.roadmap_id == r.id)
        .all()
    )
    
    # Sort grouped by phase ('learn', 'practice', 'apply') in order_index
    phase_order = {"learn": 1, "practice": 2, "apply": 3}
    tasks_query.sort(key=lambda x: (phase_order.get(x[0].phase, 99), x[0].order_index))
    
    task_responses = []
    for t, sname in tasks_query:
        # Pydantic conversion
        tr = RoadmapTaskResponse.model_validate(t)
        tr.skill_name = sname
        task_responses.append(tr)
        
    tot = r.total_tasks if r.total_tasks else 1
    comp = r.completed_tasks if r.completed_tasks else 0
    pct = (comp / tot * 100) if tot > 0 else 0.0
    
    return RoadmapResponse(
        id=r.id,
        user_id=r.user_id,
        job_role=r.job_role,
        version=r.version,
        status=r.status,
        completion_percentage=pct,
        created_at=r.created_at,
        is_transition=r.is_transition,
        generated_by=r.generated_by,
        total_tasks=r.total_tasks,
        completed_tasks=r.completed_tasks,
        updated_at=r.updated_at,
        tasks=task_responses
    )

def generate_roadmap(db: Session, user_id: UUID, job_role: str) -> RoadmapResponse:
    # 1. Load skill_gaps
    gap = db.query(SkillGap).filter(SkillGap.user_id == user_id, SkillGap.job_role == job_role).first()
    if not gap:
        raise HTTPException(status_code=404, detail="Skill gap analysis not found for this role. Complete gaps first.")
        
    # 2. Preferences
    pref = db.query(StudentPreference).filter(StudentPreference.user_id == user_id).first()
    is_trans = pref.career_transition if pref else False
    
    # 3 & 4. Parse gaps & prioritize
    missing = gap.missing_skills if gap.missing_skills else []
    weak = gap.weak_skills if gap.weak_skills else []
    
    prioritized = []
    for m in missing:
        if m.get('importance') == 'must_have':
            prioritized.append(m['skill_id'])
    for w in weak: # Assuming all weak mapped skills are heavily important 
        if w.get('required', 0) > 0:
            prioritized.append(w['skill_id'])
    for m in missing:
        if m.get('importance') == 'preferred' and m['skill_id'] not in prioritized:
            prioritized.append(m['skill_id'])
            
    top_skills = prioritized[:6]
    
    # 5. Build Tasks mappings
    RES_MAP = {
        "DSA": {"url": "https://www.coursera.org/learn/algorithms-part1", "platform": "Coursera", "hours": 20},
        "Python": {"url": "https://www.coursera.org/learn/python", "platform": "Coursera", "hours": 15},
        "Machine Learning": {"url": "https://www.coursera.org/learn/machine-learning", "platform": "Coursera", "hours": 30},
        "Deep Learning": {"url": "https://www.coursera.org/specializations/deep-learning", "platform": "Coursera", "hours": 25},
        "SQL": {"url": "https://www.kaggle.com/learn/intro-to-sql", "platform": "Kaggle", "hours": 10},
        "PostgreSQL": {"url": "https://www.kaggle.com/learn/intro-to-sql", "platform": "Kaggle", "hours": 10},
        "DBMS": {"url": "https://www.kaggle.com/learn/intro-to-sql", "platform": "Kaggle", "hours": 10},
        "Docker": {"url": "https://www.udemy.com/course/docker-mastery", "platform": "Udemy", "hours": 12},
        "AWS": {"url": "https://www.coursera.org/learn/aws-fundamentals", "platform": "Coursera", "hours": 20},
        "Git": {"url": "https://www.udemy.com/course/git-complete", "platform": "Udemy", "hours": 8},
        "React": {"url": "https://www.coursera.org/learn/front-end-react", "platform": "Coursera", "hours": 20},
        "System Design": {"url": "https://www.educative.io/courses/grokking-the-system-design-interview", "platform": "Educative", "hours": 15},
    }
    
    PRAC_MAP = {
        "DSA": {"url": "https://leetcode.com/study-plan/data-structure", "platform": "LeetCode", "hours": 10},
        "Machine Learning": {"url": "https://www.kaggle.com/competitions", "platform": "Kaggle", "hours": 8},
        "Deep Learning": {"url": "https://www.kaggle.com/competitions", "platform": "Kaggle", "hours": 8},
        "Data Analysis": {"url": "https://www.kaggle.com/competitions", "platform": "Kaggle", "hours": 8},
        "SQL": {"url": "https://leetcode.com/problemset/database", "platform": "LeetCode", "hours": 6},
    }
    
    # Resolve names
    skill_tax = db.query(SkillTaxonomy).filter(SkillTaxonomy.id.in_(top_skills)).all()
    sn_map = {str(s.id): s.skill_name for s in skill_tax}
    
    new_roadmap_id = uuid.uuid4()
    tasks_to_insert = []
    
    v_order = {"learn": 1, "practice": 1, "apply": 1}
    
    for sid in top_skills:
        sname = sn_map.get(str(sid), "Skill")
        
        # LEARN
        l_res = RES_MAP.get(sname, {"url": "https://www.coursera.org", "platform": "Coursera", "hours": 10})
        tasks_to_insert.append(RoadmapTask(
            id=uuid.uuid4(),
            roadmap_id=new_roadmap_id,
            skill_id=sid,
            phase="learn",
            task_type="course",
            title=f"Learn {sname} Fundamentals",
            resource_url=l_res["url"],
            platform=l_res["platform"],
            estimated_hours=l_res["hours"],
            order_index=v_order["learn"]
        ))
        v_order["learn"] += 1
        
        # PRACTICE
        p_res = PRAC_MAP.get(sname, {"url": "https://github.com", "platform": "GitHub", "hours": 8})
        tasks_to_insert.append(RoadmapTask(
            id=uuid.uuid4(),
            roadmap_id=new_roadmap_id,
            skill_id=sid,
            phase="practice",
            task_type="exercise",
            title=f"Practice {sname} Concepts",
            resource_url=p_res["url"],
            platform=p_res["platform"],
            estimated_hours=p_res["hours"],
            order_index=v_order["practice"]
        ))
        v_order["practice"] += 1
        
        # APPLY
        tasks_to_insert.append(RoadmapTask(
            id=uuid.uuid4(),
            roadmap_id=new_roadmap_id,
            skill_id=sid,
            phase="apply",
            task_type="project",
            title=f"Build a {sname} project and push to GitHub",
            resource_url="https://github.com",
            platform="GitHub",
            estimated_hours=12,
            order_index=v_order["apply"]
        ))
        v_order["apply"] += 1
        
    # 7. Archive old
    old_rm = db.query(Roadmap).filter(Roadmap.user_id == user_id, 
                                      Roadmap.job_role == job_role, 
                                      Roadmap.status == "active").first()
    version = 1
    if old_rm:
        old_rm.status = "archived"
        version = old_rm.version + 1
        
    # 8. Create Roadmap
    new_rm = Roadmap(
        id=new_roadmap_id,
        user_id=user_id,
        job_role=job_role,
        version=version,
        status="active",
        is_transition=is_trans,
        generated_by="system",
        total_tasks=len(tasks_to_insert),
        completed_tasks=0
    )
    db.add(new_rm)
    db.add_all(tasks_to_insert)
    db.commit()
    
    return get_roadmap(db, user_id, new_roadmap_id)

def complete_task(db: Session, user_id: UUID, task_id: UUID, feedback_score: int = None) -> RoadmapTaskResponse:
    task = db.query(RoadmapTask).join(Roadmap).filter(
        RoadmapTask.id == task_id, Roadmap.user_id == user_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if task.status != "completed":
        task.status = "completed"
        task.completed_at = datetime.utcnow()
        if feedback_score:
            task.feedback_score = feedback_score
        
        rm = db.query(Roadmap).filter(Roadmap.id == task.roadmap_id).first()
        rm.completed_tasks = (rm.completed_tasks or 0) + 1
        if rm.completed_tasks >= rm.total_tasks:
            rm.status = "completed"
            
        db.commit()
    return get_roadmap(db, user_id, task.roadmap_id).tasks[0] # Returns a reconstructed schema representation

def skip_task(db: Session, user_id: UUID, task_id: UUID) -> RoadmapTaskResponse:
    task = db.query(RoadmapTask).join(Roadmap).filter(
        RoadmapTask.id == task_id, Roadmap.user_id == user_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if task.status != "skipped":
        task.status = "skipped"
        db.commit()
    return get_roadmap(db, user_id, task.roadmap_id).tasks[0]

def add_custom_task(db: Session, user_id: UUID, roadmap_id: UUID, title: str, platform: str, estimated_hours: int, resource_url: str, phase: str) -> RoadmapTaskResponse:
    rm = db.query(Roadmap).filter(Roadmap.id == roadmap_id, Roadmap.user_id == user_id).first()
    if not rm:
        raise HTTPException(status_code=404, detail="Roadmap not found")
        
    rt = RoadmapTask(
        roadmap_id=roadmap_id,
        phase=phase,
        task_type="custom",
        title=title,
        resource_url=resource_url,
        platform=platform,
        estimated_hours=estimated_hours,
        order_index=999,
        status="pending"
    )
    db.add(rt)
    rm.total_tasks = (rm.total_tasks or 0) + 1
    db.commit()
    db.refresh(rt)
    return RoadmapTaskResponse.model_validate(rt)

def update_task_status(db: Session, user_id: UUID, task_id: UUID, status: str) -> RoadmapTaskResponse:
    task = db.query(RoadmapTask).join(Roadmap).filter(
        RoadmapTask.id == task_id, Roadmap.user_id == user_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    old_status = task.status
    task.status = status
    if status == "completed" and old_status != "completed":
        task.completed_at = datetime.utcnow()
        task.roadmap.completed_tasks = (task.roadmap.completed_tasks or 0) + 1
    elif old_status == "completed" and status != "completed":
        task.completed_at = None
        task.roadmap.completed_tasks = max(0, (task.roadmap.completed_tasks or 0) - 1)
        
    db.commit()
    db.refresh(task)
    return RoadmapTaskResponse.model_validate(task)

def delete_custom_task(db: Session, user_id: UUID, task_id: UUID):
    task = db.query(RoadmapTask).join(Roadmap).filter(
        RoadmapTask.id == task_id, Roadmap.user_id == user_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if task.task_type != "custom":
        raise HTTPException(status_code=400, detail="Only custom tasks can be deleted")
        
    rm = task.roadmap
    rm.total_tasks = max(0, (rm.total_tasks or 0) - 1)
    if task.status == "completed":
        rm.completed_tasks = max(0, (rm.completed_tasks or 0) - 1)
        
    db.delete(task)
    db.commit()
