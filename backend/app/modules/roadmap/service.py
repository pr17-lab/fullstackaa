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
from app.models.skill_resource import SkillResource
from app.models.student_skill import StudentSkill
from app.utils.academic import score_to_level
from app.modules.skills.engine import compute_gaps_for_student
from app.core.config import settings
import logging
import httpx
import json

logger = logging.getLogger(__name__)

async def generate_resources_with_llm(skill_name: str) -> dict:
    prompt = f"""You are a career mentor.

Suggest high-quality learning resources for the skill: {skill_name}

Requirements:
- 1 learning resource (course/tutorial)
- 1 practice resource (coding/practice platform)
- Prefer well-known platforms (Coursera, YouTube, LeetCode, etc.)
- Keep results concise and practical

Return ONLY JSON:
{{
  "learn": {{
    "platform": "...",
    "url": "...",
    "estimated_hours": 10
  }},
  "practice": {{
    "platform": "...",
    "url": "...",
    "estimated_hours": 10
  }}
}}"""

    if not settings.GEMINI_API_KEY:
        raise Exception("GEMINI_API_KEY not configured")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "response_mime_type": "application/json"},
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
                
        return json.loads(raw.strip())

async def get_resources_for_skill(db: Session, skill_id: UUID, skill_name: str):
    # 1. Query SkillResource
    learn_res = db.query(SkillResource).filter(SkillResource.skill_id == skill_id, SkillResource.phase == "learn").first()
    prac_res = db.query(SkillResource).filter(SkillResource.skill_id == skill_id, SkillResource.phase == "practice").first()
    
    # 2. If BOTH exist: return them
    if learn_res and prac_res:
        return learn_res, prac_res
        
    # 3. ELSE: call generate_resources_with_llm
    try:
        llm_result = await generate_resources_with_llm(skill_name)
    except Exception as e:
        logger.error(f"Gemini resource generation failed for {skill_name}: {e}")
        llm_result = None
        
    # 5. Fallback safety
    if not llm_result:
        llm_result = {
            "learn": {"url": "https://www.coursera.org", "platform": "Coursera", "estimated_hours": 10},
            "practice": {"url": "https://leetcode.com", "platform": "LeetCode", "estimated_hours": 8}
        }
        
    # 3 & 4. Create and store resources
    if not learn_res:
        learn_data = llm_result.get("learn", {})
        learn_res = SkillResource(
            skill_id=skill_id, 
            phase="learn", 
            platform=learn_data.get("platform", "Coursera")[:100],
            resource_url=learn_data.get("url", "https://www.coursera.org")[:500],
            estimated_hours=learn_data.get("estimated_hours") or learn_data.get("hours") or 10
        )
        db.add(learn_res)
        
    if not prac_res:
        prac_data = llm_result.get("practice", {})
        prac_res = SkillResource(
            skill_id=skill_id, 
            phase="practice", 
            platform=prac_data.get("platform", "LeetCode")[:100],
            resource_url=prac_data.get("url", "https://leetcode.com")[:500],
            estimated_hours=prac_data.get("estimated_hours") or prac_data.get("hours") or 8
        )
        db.add(prac_res)
        
    db.commit()
    db.refresh(learn_res)
    db.refresh(prac_res)
    
    return learn_res, prac_res
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

async def generate_roadmap(db: Session, user_id: UUID, job_role: str) -> RoadmapResponse:
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
    
    # Resolve names
    skill_tax = db.query(SkillTaxonomy).filter(SkillTaxonomy.id.in_(top_skills)).all()
    sn_map = {str(s.id): s.skill_name for s in skill_tax}
    
    new_roadmap_id = uuid.uuid4()
    tasks_to_insert = []
    
    v_order = {"learn": 1, "practice": 1, "apply": 1}
    
    for sid in top_skills:
        sname = sn_map.get(str(sid), "Skill")
        
        # Determine resources from Database or LLM
        learn_res, prac_res = await get_resources_for_skill(db, sid, sname)
            
        # LEARN
        tasks_to_insert.append(RoadmapTask(
            id=uuid.uuid4(),
            roadmap_id=new_roadmap_id,
            skill_id=sid,
            associated_skill_id=sid,
            phase="learn",
            task_type="learn",
            title=f"Learn {sname} Fundamentals",
            resource_url=learn_res.resource_url,
            platform=learn_res.platform,
            estimated_hours=learn_res.estimated_hours,
            order_index=v_order["learn"]
        ))
        v_order["learn"] += 1
        
        # PRACTICE
        tasks_to_insert.append(RoadmapTask(
            id=uuid.uuid4(),
            roadmap_id=new_roadmap_id,
            skill_id=sid,
            associated_skill_id=sid,
            phase="practice",
            task_type="practice",
            title=f"Practice {sname} Concepts",
            resource_url=prac_res.resource_url,
            platform=prac_res.platform,
            estimated_hours=prac_res.estimated_hours,
            order_index=v_order["practice"]
        ))
        v_order["practice"] += 1
        
        # APPLY
        tasks_to_insert.append(RoadmapTask(
            id=uuid.uuid4(),
            roadmap_id=new_roadmap_id,
            skill_id=sid,
            associated_skill_id=sid,
            phase="apply",
            task_type="apply",
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
        generated_by="ai_engine",
        total_tasks=len(tasks_to_insert),
        completed_tasks=0
    )
    db.add(new_rm)
    db.add_all(tasks_to_insert)
    db.commit()
    
    return get_roadmap(db, user_id, new_roadmap_id)

def _update_skill_on_task_completion(db: Session, user_id: UUID, skill_id: UUID):
    student_skill = db.query(StudentSkill).filter(
        StudentSkill.user_id == user_id, 
        StudentSkill.skill_id == skill_id
    ).first()
    
    bump_amount = 15.0 # Boost score upon completing a roadmap task
    is_sqlite = db.bind.dialect.name == "sqlite"
    
    if not student_skill:
        new_score = 50.0 + bump_amount
        student_skill = StudentSkill(
            id=uuid.uuid4(),
            user_id=user_id,
            skill_id=skill_id,
            confidence_score=new_score,
            level=score_to_level(new_score),
            source=["roadmap"] if not is_sqlite else None,
            resume_weight=0.0,
            project_weight=0.0,
            interview_weight=0.0,
            communication_weight=0.0
        )
        db.add(student_skill)
    else:
        current_score = float(student_skill.confidence_score) if student_skill.confidence_score else 0.0
        student_skill.confidence_score = min(100.0, current_score + bump_amount)
        student_skill.level = score_to_level(student_skill.confidence_score)
        
        sources = list(student_skill.source) if student_skill.source else []
        if "roadmap" not in sources:
            sources.append("roadmap")
        if not is_sqlite:
            student_skill.source = sources
        
    db.commit()
    compute_gaps_for_student(db, str(user_id))

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
            
        if task.skill_id:
            _update_skill_on_task_completion(db, user_id, task.skill_id)
            
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
        if task.skill_id:
            _update_skill_on_task_completion(db, user_id, task.skill_id)
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

def delete_roadmap(db: Session, user_id: UUID, roadmap_id: UUID):
    rm = db.query(Roadmap).filter(Roadmap.id == roadmap_id, Roadmap.user_id == user_id).first()
    if not rm:
        raise HTTPException(status_code=404, detail="Roadmap not found")
        
    # Delete associated tasks
    db.query(RoadmapTask).filter(RoadmapTask.roadmap_id == roadmap_id).delete()
    
    # Delete the roadmap
    db.delete(rm)
    db.commit()

def get_active_roadmap(db: Session, user_id: UUID) -> Roadmap:
    """Return the most recent active roadmap for a user."""
    return db.query(Roadmap).filter(
        Roadmap.user_id == user_id, 
        Roadmap.status == "active"
    ).order_by(Roadmap.created_at.desc()).first()

async def update_roadmap_with_weak_skills(db: Session, roadmap: Roadmap, weak_skills: List[str]) -> dict:
    """Update an existing active roadmap with new tasks for identified weak skills."""
    if not weak_skills:
        return {"message": "No weak skills to update", "added_skills": [], "total_tasks": roadmap.total_tasks}
        
    import sqlalchemy as sa
    
    added_skills = []
    tasks_to_insert = []
    
    # We will append new tasks to the end of each phase
    # A simple approach is just to set order_index to a high number, but let's query the current max
    max_order = db.query(sa.func.max(RoadmapTask.order_index)).filter(RoadmapTask.roadmap_id == roadmap.id).scalar()
    current_order = (max_order or 0) + 1
    
    for topic in weak_skills:
        # Match topic to skill
        tax = (
            db.query(SkillTaxonomy)
            .filter(
                sa.or_(
                    sa.func.lower(SkillTaxonomy.skill_name) == topic.lower(),
                    sa.func.array_to_string(SkillTaxonomy.aliases, ",").ilike(f"%{topic}%"),
                )
            )
            .first()
        )
        if not tax:
            continue
            
        sid = tax.id
        sname = tax.skill_name
        
        # Check if skill already exists in this roadmap
        existing = db.query(RoadmapTask).filter(
            RoadmapTask.roadmap_id == roadmap.id,
            RoadmapTask.skill_id == sid
        ).first()
        
        if existing:
            continue
            
        # Skill is NEW to this roadmap. Get resources (uses DB first, then LLM).
        learn_res, prac_res = await get_resources_for_skill(db, sid, sname)
        
        tasks_to_insert.append(RoadmapTask(
            id=uuid.uuid4(),
            roadmap_id=roadmap.id,
            skill_id=sid,
            associated_skill_id=sid,
            phase="learn",
            task_type="learn",
            title=f"Learn {sname} fundamentals",
            resource_url=learn_res.resource_url,
            platform=learn_res.platform,
            estimated_hours=learn_res.estimated_hours,
            order_index=current_order,
            status="pending"
        ))
        current_order += 1
        
        tasks_to_insert.append(RoadmapTask(
            id=uuid.uuid4(),
            roadmap_id=roadmap.id,
            skill_id=sid,
            associated_skill_id=sid,
            phase="practice",
            task_type="practice",
            title=f"Practice {sname} problems",
            resource_url=prac_res.resource_url,
            platform=prac_res.platform,
            estimated_hours=prac_res.estimated_hours,
            order_index=current_order,
            status="pending"
        ))
        current_order += 1
        
        tasks_to_insert.append(RoadmapTask(
            id=uuid.uuid4(),
            roadmap_id=roadmap.id,
            skill_id=sid,
            associated_skill_id=sid,
            phase="apply",
            task_type="apply",
            title=f"Build a mini project using {sname}",
            resource_url="https://github.com",
            platform="GitHub",
            estimated_hours=12,
            order_index=current_order,
            status="pending"
        ))
        current_order += 1
        
        added_skills.append(sname)
        
    if tasks_to_insert:
        db.add_all(tasks_to_insert)
        roadmap.total_tasks = (roadmap.total_tasks or 0) + len(tasks_to_insert)
        db.commit()
        
    return {
        "message": "Roadmap updated based on your latest interview performance" if added_skills else "Roadmap checked, no new tasks needed.",
        "added_skills": added_skills,
        "total_tasks": roadmap.total_tasks
    }
