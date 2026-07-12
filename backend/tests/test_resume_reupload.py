import uuid
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.models.skill_taxonomy import SkillTaxonomy
from app.models.student_skill import StudentSkill
from app.modules.skills.engine import calculate_composite_score
from app.utils.academic import score_to_level

def _get_or_create_skill(db_session, skill_name, category, skill_type):
    skill = db_session.query(SkillTaxonomy).filter(SkillTaxonomy.skill_name == skill_name).first()
    if not skill:
        skill = SkillTaxonomy(
            id=uuid.uuid4(),
            skill_name=skill_name,
            category=category,
            skill_type=skill_type
        )
        db_session.add(skill)
        db_session.commit()
        db_session.refresh(skill)
    return skill

@pytest.mark.asyncio
async def test_create_session_without_resume_text_param(auth_client, db_session, sample_user, sample_student_profile):
    is_sqlite = db_session.bind.dialect.name == "sqlite"
    
    # 1. Seed SkillTaxonomy entries
    t_fastapi = _get_or_create_skill(db_session, "FastAPI", "backend", "tool")
    t_react = _get_or_create_skill(db_session, "React", "frontend", "tool")

    # 2. Seed StudentSkill entries for user
    ss_fastapi = StudentSkill(
        user_id=sample_user.id,
        skill_id=t_fastapi.id,
        resume_weight=70.0,
        project_weight=50.0,
        interview_weight=0.0,
        confidence_score=60.0,
        level="strong",
        source=None if is_sqlite else ["resume"]
    )
    ss_react = StudentSkill(
        user_id=sample_user.id,
        skill_id=t_react.id,
        resume_weight=70.0,
        project_weight=0.0,
        interview_weight=0.0,
        confidence_score=70.0,
        level="strong",
        source=None if is_sqlite else ["resume"]
    )
    db_session.add_all([ss_fastapi, ss_react])
    db_session.commit()

    # 3. Intercept generate_questions_async to verify parameters
    from app.modules.interview.service import InterviewService
    captured_skills = []

    async def mock_generate(self, *, branch, semester, jd_text="", resume_context=None, student_skills=None, limit=10, on_chunk=None):
        nonlocal captured_skills
        if student_skills:
            captured_skills = list(student_skills)
        return [{"topic": "FastAPI", "question": "Explain FastAPI dependency injection.", "difficulty": "medium"}], "mock"

    with patch.object(InterviewService, "generate_questions_async", mock_generate):
        response = auth_client.post(
            "/api/interview/sessions",
            json={
                "jd_text": "Need a FastAPI and React developer",
                "limit": 1
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert len(data["questions"]) > 0
        
        # Verify student skills were queried and passed correctly
        assert len(captured_skills) == 2
        skill_ids = [s.skill_id for s in captured_skills]
        assert t_fastapi.id in skill_ids
        assert t_react.id in skill_ids


@pytest.mark.asyncio
async def test_resume_reupload_behavior(auth_client, db_session, sample_user, sample_student_profile):
    is_sqlite = db_session.bind.dialect.name == "sqlite"
    
    # 1. Seed SkillTaxonomy
    t_fastapi = _get_or_create_skill(db_session, "FastAPI", "backend", "tool")
    t_react = _get_or_create_skill(db_session, "React", "frontend", "tool")
    t_docker = _get_or_create_skill(db_session, "Docker", "cloud_devops", "tool")
    t_sql = _get_or_create_skill(db_session, "SQL", "database", "tool")

    # 2. Seed StudentSkill rows
    # - FastAPI: resume-sourced (resume_weight=70.0), but no longer appears in new resume
    ss_fastapi = StudentSkill(
        user_id=sample_user.id,
        skill_id=t_fastapi.id,
        resume_weight=70.0,
        project_weight=50.0,
        interview_weight=60.0,
        is_interview_scored=True,
        confidence_score=calculate_composite_score(70.0, 50.0, 60.0, 0.0, True),
        level="strong",
        source=None if is_sqlite else ["resume"]
    )
    # - React: resume-sourced (resume_weight=70.0), and still appears in new resume
    ss_react = StudentSkill(
        user_id=sample_user.id,
        skill_id=t_react.id,
        resume_weight=70.0,
        project_weight=0.0,
        interview_weight=0.0,
        is_interview_scored=False,
        confidence_score=calculate_composite_score(70.0, 0.0, 0.0, 0.0, False),
        level="strong",
        source=None if is_sqlite else ["resume"]
    )
    # - Docker: not resume-sourced (resume_weight=0.0), has project weight
    ss_docker = StudentSkill(
        user_id=sample_user.id,
        skill_id=t_docker.id,
        resume_weight=0.0,
        project_weight=40.0,
        interview_weight=80.0,
        is_interview_scored=True,
        confidence_score=calculate_composite_score(0.0, 40.0, 80.0, 0.0, True),
        level="strong",
        source=None if is_sqlite else ["project"]
    )
    db_session.add_all([ss_fastapi, ss_react, ss_docker])
    db_session.commit()

    # We patch Gemini to return React and SQL (React still appears, SQL is new, FastAPI no longer appears)
    import json
    import httpx
    
    mock_gemini_resp = MagicMock()
    mock_gemini_resp.raise_for_status = MagicMock()
    mock_gemini_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps(["React", "SQL"])
                        }
                    ]
                }
            }
        ]
    }

    with patch("app.core.config.settings.GEMINI_API_KEY", "mock-key"), \
         patch("httpx.AsyncClient.post", return_value=mock_gemini_resp):
        
        response = auth_client.post(
            "/api/skills/extract-resume-skills",
            json={"resume_text": "Experienced in React and SQL."}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True

        # Query all student skills from DB to verify weights
        skills = db_session.query(StudentSkill).filter(StudentSkill.user_id == sample_user.id).all()
        skills_dict = {s.skill_id: s for s in skills}

        # React: still appears
        assert t_react.id in skills_dict
        react_ss = skills_dict[t_react.id]
        assert float(react_ss.resume_weight) == 70.0
        assert float(react_ss.project_weight) == 0.0
        assert float(react_ss.interview_weight) == 0.0

        # SQL: newly added
        assert t_sql.id in skills_dict
        sql_ss = skills_dict[t_sql.id]
        assert float(sql_ss.resume_weight) == 70.0
        assert float(sql_ss.project_weight) == 0.0
        assert float(sql_ss.interview_weight) == 0.0

        # FastAPI: no longer appears, weight zeroed out, project and interview weights untouched
        assert t_fastapi.id in skills_dict
        fastapi_ss = skills_dict[t_fastapi.id]
        assert float(fastapi_ss.resume_weight) == 0.0
        assert float(fastapi_ss.project_weight) == 50.0
        assert float(fastapi_ss.interview_weight) == 60.0
        expected_fastapi_score = calculate_composite_score(0.0, 50.0, 60.0, 0.0, is_interview_scored=True)
        assert float(fastapi_ss.confidence_score) == expected_fastapi_score
        assert fastapi_ss.level == score_to_level(expected_fastapi_score)

        # Docker: untouched
        assert t_docker.id in skills_dict
        docker_ss = skills_dict[t_docker.id]
        assert float(docker_ss.resume_weight) == 0.0
        assert float(docker_ss.project_weight) == 40.0
        assert float(docker_ss.interview_weight) == 80.0
