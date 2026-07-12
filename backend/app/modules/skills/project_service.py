"""
Service for GitHub repository metadata parsing, structural complexity scoring,
and Gemini-based technology/skill tag extraction.
"""

import base64
import json
import logging
from datetime import datetime
import uuid
from uuid import UUID

import httpx
import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.student_project import StudentProject
from app.models.student_skill import StudentSkill
from app.models.skill_taxonomy import SkillTaxonomy
from app.models.roadmap import Roadmap, RoadmapTask
from app.modules.skills.engine import calculate_composite_score
from app.utils.academic import score_to_level

logger = logging.getLogger(__name__)


def parse_repo_url(repo_url: str) -> tuple[str, str]:
    """
    Extract owner and repository name from a github.com URL.
    Returns (owner, repo).
    Raises ValueError if URL format is invalid.
    """
    url_clean = repo_url.strip().rstrip("/")
    if url_clean.endswith(".git"):
        url_clean = url_clean[:-4]

    # Split by github.com/
    parts = url_clean.split("github.com/")
    if len(parts) < 2:
        raise ValueError("Invalid GitHub URL: must contain github.com/")

    path_parts = parts[1].split("/")
    if len(path_parts) < 2:
        raise ValueError("Invalid GitHub URL: owner and repository name not found")

    owner = path_parts[0]
    repo = path_parts[1]
    return owner, repo


async def verify_github_complexity_async(repo_url: str, user_id: UUID, db: Session, task_id: UUID = None) -> None:
    """
    Asynchronously verify a GitHub repository's structural complexity,
    extract framework and tool tags via Gemini 1.5 Flash,
    and persist/update the StudentProject record in the database.
    """
    def _fail_task():
        if task_id:
            try:
                task = db.query(RoadmapTask).filter(RoadmapTask.id == task_id).first()
                if task:
                    task.validation_status = "failed"
                    task.status = "pending"
                    db.commit()
            except Exception as db_exc:
                logger.error("Failed to update task to failed in db: %s", db_exc)

    try:
        owner, repo = parse_repo_url(repo_url)
    except ValueError as exc:
        logger.error("Failed to parse repo URL %s: %s", repo_url, exc)
        _fail_task()
        return

    headers = {
        "User-Agent": "SATA-Career-Intelligence-Platform",
        "Accept": "application/vnd.github.v3+json"
    }

    # Include GitHub token if configured (optional but robust for rate limits)
    # Since we don't have a token, we just rely on public API
    
    score = 0
    repo_description = ""
    readme_content = ""
    commits_count = 0
    has_devops = False
    has_testing = False
    has_boundaries = False

    async with httpx.AsyncClient(timeout=15.0) as client:
        # 1. Base Repository Check (+20 points)
        try:
            repo_url_api = f"https://api.github.com/repos/{owner}/{repo}"
            resp_repo = await client.get(repo_url_api, headers=headers)
            if resp_repo.status_code == 200:
                score += 20
                repo_data = resp_repo.json()
                repo_description = repo_data.get("description") or ""
            else:
                logger.warning(
                    "GitHub repository base check failed for %s/%s (Status %d)",
                    owner, repo, resp_repo.status_code
                )
                _fail_task()
                return
        except Exception as exc:
            logger.error("Exception during GitHub base repository check: %s", exc)
            _fail_task()
            return

        # 2. Commit History Multiplier (+20 points)
        try:
            commits_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
            resp_commits = await client.get(commits_url, headers=headers)
            if resp_commits.status_code == 200:
                commits = resp_commits.json()
                commits_count = len(commits) if isinstance(commits, list) else 0
                if commits_count > 30:
                    score += 20
                elif commits_count >= 10:
                    score += 10
                else:
                    score += 5
            else:
                logger.warning("Failed to retrieve commits for %s/%s", owner, repo)
                score += 5
        except Exception as exc:
            logger.error("Exception during GitHub commits retrieve: %s", exc)
            score += 5

        # 3. Architectural Nodes Evaluation (+40 points)
        try:
            contents_url = f"https://api.github.com/repos/{owner}/{repo}/contents"
            resp_contents = await client.get(contents_url, headers=headers)
            if resp_contents.status_code == 200:
                contents = resp_contents.json()
                if isinstance(contents, list):
                    root_names = {item.get("name", "").lower(): item for item in contents}
                    
                    # DevOps scan: Dockerfile, docker-compose.yml, .github
                    if ("dockerfile" in root_names or 
                            "docker-compose.yml" in root_names or 
                            ".github" in root_names):
                        has_devops = True
                        score += 15

                    # Testing scan: pytest.ini, conftest.py, jest.config.js, tests
                    if ("pytest.ini" in root_names or 
                            "conftest.py" in root_names or 
                            "jest.config.js" in root_names or 
                            "tests" in root_names):
                        has_testing = True
                        score += 15

                    # Boundaries scan: auth, middleware, services
                    if ("auth" in root_names or 
                            "middleware" in root_names or 
                            "services" in root_names):
                        has_boundaries = True
                        score += 10
            else:
                logger.warning("Failed to retrieve contents for %s/%s", owner, repo)
        except Exception as exc:
            logger.error("Exception during GitHub contents scan: %s", exc)

        # 4. Documentation Volume (+20 points)
        try:
            readme_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
            resp_readme = await client.get(readme_url, headers=headers)
            if resp_readme.status_code == 200:
                readme_data = resp_readme.json()
                b64_content = readme_data.get("content", "").replace("\n", "").replace(" ", "")
                if b64_content:
                    readme_bytes = base64.b64decode(b64_content)
                    readme_content = readme_bytes.decode("utf-8", errors="ignore")
                    readme_len = len(readme_content)
                    if readme_len > 2000:
                        score += 20
                    elif readme_len >= 500:
                        score += 10
            else:
                logger.warning("No README found for %s/%s", owner, repo)
        except Exception as exc:
            logger.error("Exception during GitHub README retrieval: %s", exc)

    # 5. Trigger Gemini Skill Tag Extraction
    extracted_skills = []
    if readme_content and settings.GEMINI_API_KEY:
        try:
            url_gemini = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
            )
            prompt = f"""Act as an automated technology identifier. Read this project README. Return ONLY a plain JSON array of framework, tool, or database strings discovered (e.g., ['FastAPI', 'React', 'Docker']). Do not include explanatory text or markdown backticks.

README:
{readme_content[:4000]}"""

            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.3, 
                    "response_mime_type": "application/json"
                },
            }
            async with httpx.AsyncClient(timeout=25.0) as client_http:
                resp_gemini = await client_http.post(url_gemini, json=payload)
                resp_gemini.raise_for_status()
                raw_text = resp_gemini.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                
                # Strip markdown code fences if Gemini returned them anyway
                if raw_text.startswith("```"):
                    raw_text = raw_text.split("```")[1]
                    if raw_text.startswith("json"):
                        raw_text = raw_text[4:]
                raw_text = raw_text.strip()
                
                extracted_skills = json.loads(raw_text)
                if not isinstance(extracted_skills, list):
                    extracted_skills = []
        except Exception as exc:
            logger.error("Exception during Gemini skill extraction: %s", exc)
            # Fallback based on tech stack check
            extracted_skills = []

    # 6. Save or Update StudentProject in the DB
    try:
        project = (
            db.query(StudentProject)
            .filter(
                StudentProject.user_id == user_id,
                StudentProject.repo_url == repo_url
            )
            .first()
        )

        now = datetime.utcnow()
        title_val = repo.replace("-", " ").replace("_", " ").title() + " Repository"

        is_sqlite = db.bind.dialect.name == "sqlite"
        if project:
            project.calculated_complexity = score
            project.extracted_skills = extracted_skills
            project.analyzed_at = now
            if not is_sqlite:
                project.tech_stack = extracted_skills
            if repo_description:
                project.description = repo_description
        else:
            project = StudentProject(
                user_id=user_id,
                title=title_val,
                description=repo_description or "GitHub Integrated Repository",
                repo_url=repo_url,
                extracted_skills=extracted_skills,
                calculated_complexity=score,
                analyzed_at=now,
                tech_stack=extracted_skills if not is_sqlite else None,
                domain="GitHub Integration"
            )
            db.add(project)

        db.commit()
        db.refresh(project)
        logger.info(
            "GitHub Repository Ingested successfully: user=%s, repo=%s/%s, complexity=%d, skills=%s",
            user_id, owner, repo, score, extracted_skills
        )

        # 7. Synchronize weights to StudentSkill Matrix
        if extracted_skills:
            logger.info("Synchronizing GitHub extracted skills to user %s skill matrix", user_id)
            for skill_name in extracted_skills:
                # Dialect-safe case-insensitive/aliases lookup in SkillTaxonomy
                if db.bind.dialect.name == "sqlite":
                    tax = (
                        db.query(SkillTaxonomy)
                        .filter(sa.func.lower(SkillTaxonomy.skill_name) == skill_name.lower())
                        .first()
                    )
                    if not tax:
                        all_tax = db.query(SkillTaxonomy).all()
                        for t in all_tax:
                            if t.aliases and any(skill_name.lower() in str(a).lower() for a in t.aliases):
                                tax = t
                                break
                else:
                    tax = (
                        db.query(SkillTaxonomy)
                        .filter(
                            sa.or_(
                                sa.func.lower(SkillTaxonomy.skill_name) == skill_name.lower(),
                                sa.func.array_to_string(SkillTaxonomy.aliases, ",").ilike(f"%{skill_name}%"),
                            )
                        )
                        .first()
                    )

                if not tax:
                    logger.warning("Skill '%s' not found in SkillTaxonomy, skipping synchronization", skill_name)
                    continue

                # Find or initialize StudentSkill row for this user
                ss = (
                    db.query(StudentSkill)
                    .filter(
                        StudentSkill.user_id == user_id,
                        StudentSkill.skill_id == tax.id
                    )
                    .first()
                )
                if not ss:
                    ss = StudentSkill(
                        id=uuid.uuid4(),
                        user_id=user_id,
                        skill_id=tax.id,
                        resume_weight=0.0,
                        project_weight=0.0,
                        interview_weight=0.0,
                        communication_weight=0.0,
                        source=["project"] if not is_sqlite else None
                    )
                    db.add(ss)
                    db.flush()
                else:
                    # Ensure "project" is in source list
                    src_list = list(ss.source) if ss.source else []
                    if "project" not in src_list:
                        src_list.append("project")
                        if not is_sqlite:
                            ss.source = src_list

                # Update project weight
                ss.project_weight = float(score)

                # Capture weights
                res_wt = float(ss.resume_weight) if ss.resume_weight else 0.0
                pr_wt = float(ss.project_weight) if ss.project_weight else 0.0
                in_wt = float(ss.interview_weight) if ss.interview_weight else 0.0
                comm_wt = float(ss.communication_weight) if ss.communication_weight else 0.0

                # Import and execute the Phase 4 calculate_composite_score function
                new_conf = calculate_composite_score(res_wt, pr_wt, in_wt, comm_wt, is_interview_scored=ss.is_interview_scored)
                ss.confidence_score = new_conf

                # Update level and last computed timestamp
                ss.level = score_to_level(ss.confidence_score)
                ss.last_computed_at = datetime.utcnow()

            db.commit()
            logger.info("Successfully completed composite calibration loop for user %s", user_id)

        # Update the task status to verified and completed if task_id is provided
        if task_id:
            try:
                task = db.query(RoadmapTask).filter(RoadmapTask.id == task_id).first()
                if task:
                    task.validation_status = "verified"
                    task.status = "completed"
                    task.completed_at = datetime.utcnow()
                    
                    # Update roadmap completed tasks
                    rm = task.roadmap
                    if rm:
                        rm.completed_tasks = (rm.completed_tasks or 0) + 1
                        if rm.completed_tasks >= rm.total_tasks:
                            rm.status = "completed"
                    
                    # Calibrate skill on task completion
                    if task.skill_id:
                        from app.modules.roadmap.service import _update_skill_on_task_completion
                        _update_skill_on_task_completion(db, user_id, task.skill_id)
                    
                    db.commit()
                    logger.info("Successfully updated RoadmapTask %s to verified and completed", task_id)
            except Exception as task_exc:
                logger.error("Failed to update RoadmapTask on success: %s", task_exc)

    except Exception as exc:
        db.rollback()
        logger.error("Failed to save ingested student project to database: %s", exc)
        if task_id:
            try:
                task = db.query(RoadmapTask).filter(RoadmapTask.id == task_id).first()
                if task:
                    task.validation_status = "failed"
                    task.status = "pending"
                    db.commit()
            except Exception as db_exc:
                logger.error("Failed to update task to failed in db rollback block: %s", db_exc)
