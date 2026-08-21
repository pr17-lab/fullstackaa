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
from app.models.learning_resource import LearningResource
from app.models.student_skill import StudentSkill
from app.utils.academic import score_to_level
from app.modules.skills.engine import compute_gaps_for_student
from app.core.config import settings
from typing import Optional

class SkillResourceContainer:
    def __init__(self, resource_url: str, platform: str, estimated_hours: int, resource_source: str, learning_resource_id: Optional[UUID] = None):
        self.resource_url = resource_url
        self.platform = platform
        self.estimated_hours = estimated_hours
        self.resource_source = resource_source
        self.learning_resource_id = learning_resource_id
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

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "response_mime_type": "application/json"},
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, json=payload, headers={"x-goog-api-key": settings.GEMINI_API_KEY})
        resp.raise_for_status()
        raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
                
        return json.loads(raw.strip())

async def get_resources_for_skill(db: Session, skill_id: UUID, skill_name: str):
    # 1. Query LearningResource (curated) first
    curated_learn = db.query(LearningResource).filter(
        LearningResource.skill_id == skill_id,
        LearningResource.phase == "learn"
    ).order_by((LearningResource.upvotes - LearningResource.downvotes).desc()).first()

    curated_prac = db.query(LearningResource).filter(
        LearningResource.skill_id == skill_id,
        LearningResource.phase == "practice"
    ).order_by((LearningResource.upvotes - LearningResource.downvotes).desc()).first()

    # Determine containers
    if curated_learn:
        learn_container = SkillResourceContainer(
            resource_url=curated_learn.resource_url,
            platform=curated_learn.platform,
            estimated_hours=10,
            resource_source="curated",
            learning_resource_id=curated_learn.id
        )
    else:
        # Fall back to SkillResource cache next
        lr_cached = db.query(SkillResource).filter(SkillResource.skill_id == skill_id, SkillResource.phase == "learn").first()
        if lr_cached:
            learn_container = SkillResourceContainer(
                resource_url=lr_cached.resource_url,
                platform=lr_cached.platform,
                estimated_hours=lr_cached.estimated_hours,
                resource_source="ai_suggested",
                learning_resource_id=None
            )
        else:
            learn_container = None

    if curated_prac:
        prac_container = SkillResourceContainer(
            resource_url=curated_prac.resource_url,
            platform=curated_prac.platform,
            estimated_hours=8,
            resource_source="curated",
            learning_resource_id=curated_prac.id
        )
    else:
        # Fall back to SkillResource cache next
        pr_cached = db.query(SkillResource).filter(SkillResource.skill_id == skill_id, SkillResource.phase == "practice").first()
        if pr_cached:
            prac_container = SkillResourceContainer(
                resource_url=pr_cached.resource_url,
                platform=pr_cached.platform,
                estimated_hours=pr_cached.estimated_hours,
                resource_source="ai_suggested",
                learning_resource_id=None
            )
        else:
            prac_container = None

    # 2. If BOTH containers exist, return them immediately
    if learn_container and prac_container:
        return learn_container, prac_container

    # 3. Otherwise: call generate_resources_with_llm for any missing phase
    try:
        llm_result = await generate_resources_with_llm(skill_name)
    except Exception as e:
        logger.error(f"Gemini resource generation failed for {skill_name}: {e}")
        llm_result = None

    if not llm_result:
        llm_result = {
            "learn": {"url": "https://www.coursera.org", "platform": "Coursera", "estimated_hours": 10},
            "practice": {"url": "https://leetcode.com", "platform": "LeetCode", "estimated_hours": 8}
        }

    # Populate learn container
    if not learn_container:
        learn_data = llm_result.get("learn", {})
        plat = learn_data.get("platform", "Coursera")[:100]
        url = learn_data.get("url", "https://www.coursera.org")[:500]
        hours = learn_data.get("estimated_hours") or learn_data.get("hours") or 10
        
        lr_new = SkillResource(
            skill_id=skill_id,
            phase="learn",
            platform=plat,
            resource_url=url,
            estimated_hours=hours
        )
        db.add(lr_new)
        learn_container = SkillResourceContainer(
            resource_url=url,
            platform=plat,
            estimated_hours=hours,
            resource_source="ai_suggested",
            learning_resource_id=None
        )

    # Populate practice container
    if not prac_container:
        prac_data = llm_result.get("practice", {})
        plat = prac_data.get("platform", "LeetCode")[:100]
        url = prac_data.get("url", "https://leetcode.com")[:500]
        hours = prac_data.get("estimated_hours") or prac_data.get("hours") or 8
        
        pr_new = SkillResource(
            skill_id=skill_id,
            phase="practice",
            platform=plat,
            resource_url=url,
            estimated_hours=hours
        )
        db.add(pr_new)
        prac_container = SkillResourceContainer(
            resource_url=url,
            platform=plat,
            estimated_hours=hours,
            resource_source="ai_suggested",
            learning_resource_id=None
        )

    db.commit()
    return learn_container, prac_container
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
        tr = RoadmapTaskResponse.model_validate(t)
        tr.skill_name = sname
        
        tr.depth_verified = False
        tr.project_id = None
        if t.phase == "apply" and t.submission_link:
            from app.models.student_project import StudentProject
            project = db.query(StudentProject).filter(
                StudentProject.user_id == user_id,
                StudentProject.repo_url == t.submission_link
            ).first()
            if project:
                tr.depth_verified = project.depth_verified
                tr.project_id = project.id
        task_responses.append(tr)
        
    from app.models.student_preference import StudentPreference
    from app.models.behavior_summary import BehaviorSummary
    
    pref = db.query(StudentPreference).filter(StudentPreference.user_id == r.user_id).first()
    available_hours = pref.available_hours_per_week if pref else None
    
    projected_weeks = None
    pacing_status = None
    
    if available_hours is not None and available_hours > 0:
        pacing_status = "on_track"
        incomplete_hours = sum((t[0].estimated_hours or 0) for t in tasks_query if t[0].status != 'completed')
        projected_weeks = float(incomplete_hours) / available_hours
        
        behavior = db.query(BehaviorSummary).filter(BehaviorSummary.user_id == r.user_id).first()
        if behavior and behavior.last_active_at:
            dt_active = behavior.last_active_at
            dt_created = r.created_at
            if dt_active.tzinfo is not None and dt_created.tzinfo is None:
                dt_active = dt_active.replace(tzinfo=None)
            elif dt_created.tzinfo is not None and dt_active.tzinfo is None:
                dt_created = dt_created.replace(tzinfo=None)
                
            elapsed_seconds = (dt_active - dt_created).total_seconds()
            weeks_elapsed = elapsed_seconds / (7.0 * 24.0 * 3600.0)
            
            if weeks_elapsed >= 0.1:
                remaining_tasks_count = sum(1 for t in tasks_query if t[0].status != 'completed')
                if projected_weeks > 0:
                    needed_rate = remaining_tasks_count / projected_weeks
                    actual_rate = (behavior.roadmap_tasks_done or 0) / weeks_elapsed
                    if actual_rate < 0.5 * needed_rate:
                        pacing_status = "behind"
                        
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
        tasks=task_responses,
        projected_completion_weeks=projected_weeks,
        pacing_status=pacing_status
    )

async def generate_roadmap(db: Session, user_id: UUID, job_role: str) -> RoadmapResponse:
    # 1. Load skill_gaps
    gap = db.query(SkillGap).filter(SkillGap.user_id == user_id, SkillGap.job_role == job_role).first()
    if not gap:
        compute_gaps_for_student(db, str(user_id))
        gap = db.query(SkillGap).filter(SkillGap.user_id == user_id, SkillGap.job_role == job_role).first()
        
    if not gap:
        raise HTTPException(status_code=404, detail="Skill gap analysis not found for this role. Complete gaps first.")
        
    # 2. Preferences
    pref = db.query(StudentPreference).filter(StudentPreference.user_id == user_id).first()
    is_trans = pref.career_transition if pref else False
    
    # 3 & 4. Parse gaps & prioritize
    missing = gap.missing_skills if gap.missing_skills else []
    weak = gap.weak_skills if gap.weak_skills else []
    
    from app.models.job_skill_requirement import JobSkillRequirement
    reqs = db.query(JobSkillRequirement).filter(JobSkillRequirement.job_role == job_role).all()
    importance_map = {str(r.skill_id): r.importance for r in reqs}

    prioritized = []
    for m in missing:
        sid = m['skill_id']
        imp = importance_map.get(str(sid))
        if imp == 'must_have' or imp is None:
            prioritized.append(sid)
            
    for w in weak: # Assuming all weak mapped skills are heavily important 
        # In newer schema, required might not be present or different, fallback to always adding if not in prioritized
        sid = w['skill_id']
        if w.get('required', 1) > 0 and sid not in prioritized:
            prioritized.append(sid)
            
    for m in missing:
        sid = m['skill_id']
        imp = importance_map.get(str(sid))
        if imp == 'preferred' and sid not in prioritized:
            prioritized.append(sid)
            
    top_skills = prioritized[:6]
    import uuid
    top_skills_uuids = [uuid.UUID(str(sid)) for sid in top_skills]
    
    # Resolve names
    skill_tax = db.query(SkillTaxonomy).filter(SkillTaxonomy.id.in_(top_skills_uuids)).all()
    sn_map = {str(s.id): s.skill_name for s in skill_tax}
    
    new_roadmap_id = uuid.uuid4()
    tasks_to_insert = []
    
    v_order = {"learn": 1, "practice": 1, "apply": 1}
    
    for sid in top_skills_uuids:
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
            order_index=v_order["learn"],
            resource_source=learn_res.resource_source,
            learning_resource_id=learn_res.learning_resource_id
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
            title=f"Practice Interview: {sname}",
            resource_url="/interview",
            platform="Interview Platform",
            estimated_hours=prac_res.estimated_hours,
            order_index=v_order["practice"],
            resource_source="system",
            learning_resource_id=None
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
            order_index=v_order["apply"],
            resource_source="curated",
            learning_resource_id=None
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
            status="pending",
            resource_source=learn_res.resource_source,
            learning_resource_id=learn_res.learning_resource_id
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
            status="pending",
            resource_source=prac_res.resource_source,
            learning_resource_id=prac_res.learning_resource_id
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
            status="pending",
            resource_source="curated",
            learning_resource_id=None
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
