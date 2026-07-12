import uuid
from datetime import datetime
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.models.student_project import StudentProject
from app.models.interview import InterviewSession, InterviewQuestion
from app.models.skill_taxonomy import SkillTaxonomy
from app.models.student_skill import StudentSkill
from app.modules.interview.service import interview_service

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
async def test_project_session_init_pulls_context(auth_client, db_session, sample_user, sample_student_profile):
    skill = _get_or_create_skill(db_session, "React", "frontend", "tool")

    is_sqlite = db_session.bind.dialect.name == "sqlite"
    # Create a project with repo_url
    project = StudentProject(
        id=uuid.uuid4(),
        user_id=sample_user.id,
        title="SATA Platform",
        description="Career intelligence software",
        tech_stack=None if is_sqlite else ["React", "FastAPI"],
        extracted_skills=["React", "FastAPI"],
        repo_url="https://github.com/student/sata-platform",
        depth_verified=False
    )
    db_session.add(project)
    db_session.commit()

    # Mock Github API calls
    mock_contents = [{"name": "src", "type": "dir"}, {"name": "main.py", "type": "file"}]
    # Base64 encoded: "README file content with React details"
    mock_readme = {
        "content": "UkVBRE1FIGZpbGUgY29udGVudCB3aXRoIFJlYWN0IGRldGFpbHM=\n"
    }

    mock_gemini_resp = MagicMock()
    mock_gemini_resp.status_code = 200
    mock_gemini_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": '{"questions": [{"topic": "React", "question": "Walk me through how React state works in this repo?", "difficulty": "hard"}, {"topic": "FastAPI", "question": "Why FastAPI?", "difficulty": "hard"}, {"topic": "Project: SATA Platform", "question": "How does main.py work?", "difficulty": "hard"}]}'
                        }
                    ]
                }
            }
        ]
    }
    mock_gemini_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    # Mocking client.get to return contents and readme
    def mock_get_side_effect(url, *args, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        if "contents" in url:
            resp.json = MagicMock(return_value=mock_contents)
        elif "readme" in url:
            resp.json = MagicMock(return_value=mock_readme)
        else:
            resp.json = MagicMock(return_value={})
        return resp

    mock_client.get = AsyncMock(side_effect=mock_get_side_effect)
    mock_client.post = AsyncMock(return_value=mock_gemini_resp)

    with patch("app.modules.interview.service.settings.GEMINI_API_KEY", "test"), \
         patch("app.modules.interview.service.settings.GROQ_API_KEY", None), \
         patch("app.modules.interview.service.httpx.AsyncClient") as mock_class:
        mock_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_class.return_value.__aexit__ = AsyncMock(return_value=False)

        response = auth_client.post(
            "/api/interview/sessions/practice-project",
            json={
                "project_id": str(project.id),
                "limit": 3
            }
        )

    assert response.status_code == 201
    data = response.json()
    assert data["project_id"] == str(project.id)
    assert data["is_micro"] is True
    assert data["topic"] == "Project Depth Screen: SATA Platform"
    assert len(data["questions"]) == 3
    # Check that associated_skill_id is populated from React since it matches our taxonomy
    assert data["associated_skill_id"] == str(skill.id)


@pytest.mark.asyncio
async def test_project_session_completion_updates_skills_and_project_flags(db_session, sample_user, sample_student_profile):
    is_sqlite = db_session.bind.dialect.name == "sqlite"
    skill_react = _get_or_create_skill(db_session, "React", "frontend", "tool")
    skill_fastapi = _get_or_create_skill(db_session, "FastAPI", "backend", "tool")

    project = StudentProject(
        id=uuid.uuid4(),
        user_id=sample_user.id,
        title="SATA Platform",
        description="Career intelligence software",
        tech_stack=None if is_sqlite else ["React", "FastAPI"],
        extracted_skills=["React", "FastAPI"],
        repo_url="https://github.com/student/sata-platform",
        depth_verified=False
    )
    db_session.add(project)
    db_session.commit()

    # Pre-seed StudentSkills
    ss_react = StudentSkill(
        user_id=sample_user.id,
        skill_id=skill_react.id,
        resume_weight=30.0,
        project_weight=50.0,
        interview_weight=0.0,
        communication_weight=0.0,
        source=None if is_sqlite else ["resume"]
    )
    ss_fastapi = StudentSkill(
        user_id=sample_user.id,
        skill_id=skill_fastapi.id,
        resume_weight=40.0,
        project_weight=50.0,
        interview_weight=0.0,
        communication_weight=0.0,
        source=None if is_sqlite else ["resume"]
    )
    db_session.add_all([ss_react, ss_fastapi])
    db_session.commit()

    session = InterviewSession(
        user_id=sample_user.id,
        branch="CSE",
        topic="Project Depth Screen: SATA Platform",
        status="active",
        is_micro=True,
        project_id=project.id
    )
    db_session.add(session)
    db_session.flush()

    q1 = InterviewQuestion(session_id=session.id, topic="React", question="Q1", difficulty="hard", ai_score=9, user_answer="Answer 1")
    q2 = InterviewQuestion(session_id=session.id, topic="FastAPI", question="Q2", difficulty="hard", ai_score=9, user_answer="Answer 2")
    q3 = InterviewQuestion(session_id=session.id, topic="Project: SATA Platform", question="Q3", difficulty="hard", user_answer="Answer 3")
    db_session.add_all([q1, q2, q3])
    db_session.commit()

    mock_gemini_resp = MagicMock()
    mock_gemini_resp.status_code = 200
    mock_gemini_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": '{"technical_score": 9, "communication_score": 9, "verdict": "Strong", "feedback": "Good", "mistakes": [], "improvement": "None", "model_answer": "Model"}'
                        }
                    ]
                }
            }
        ]
    }
    mock_gemini_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_gemini_resp)

    with patch("app.modules.interview.service.settings.GEMINI_API_KEY", "test"), \
         patch("app.modules.interview.service.httpx.AsyncClient") as mock_class:
        mock_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_class.return_value.__aexit__ = AsyncMock(return_value=False)

        await interview_service.evaluate_single_answer_async(
            db_session,
            user_id=sample_user.id,
            session_id=session.id,
            question_id=q3.id,
            user_answer="Answer 3"
        )

    # 1. Assert project record has depth_verified = True and depth_verified_at set
    db_session.refresh(project)
    assert project.depth_verified is True
    assert project.depth_verified_at is not None

    # 2. Assert interview weights are updated on both skills mapped to the project
    db_session.refresh(ss_react)
    db_session.refresh(ss_fastapi)
    assert float(ss_react.interview_weight) == 10.0
    assert float(ss_fastapi.interview_weight) == 10.0
    if not is_sqlite:
        assert "interview" in ss_react.source
        assert "interview" in ss_fastapi.source


def test_verification_toggles_remain_independent(db_session, sample_user):
    # Tests that a project can be structurally verified but not depth verified
    project = StudentProject(
        id=uuid.uuid4(),
        user_id=sample_user.id,
        title="Independent Toggles project",
        description="Demo repo",
        repo_url="https://github.com/student/toggle-project",
        complexity="medium",
        calculated_complexity=45,
        analyzed_at=datetime.utcnow(),
        depth_verified=False
    )
    db_session.add(project)
    db_session.commit()

    # Query project directly
    db_session.refresh(project)
    # Structurally verified implies calculated_complexity and analyzed_at are not null
    assert project.calculated_complexity is not None
    assert project.analyzed_at is not None
    # Depth verification is currently False
    assert project.depth_verified is False

    # Simulate depth verification completed
    project.depth_verified = True
    project.depth_verified_at = datetime.utcnow()
    db_session.commit()

    db_session.refresh(project)
    assert project.calculated_complexity == 45
    assert project.depth_verified is True
    assert project.depth_verified_at is not None


@pytest.mark.asyncio
async def test_project_session_depth_verified_threshold_recommendation(db_session, sample_user, sample_student_profile):
    is_sqlite = db_session.bind.dialect.name == "sqlite"
    project = StudentProject(
        id=uuid.uuid4(),
        user_id=sample_user.id,
        title="Threshold Test project",
        description="Demo repo",
        repo_url="https://github.com/student/threshold-project",
        depth_verified=False
    )
    db_session.add(project)
    db_session.commit()

    # Scenario A: overall_score >= 6 and depth_verified_recommendation is True => True
    session_a = InterviewSession(
        user_id=sample_user.id,
        branch="CSE",
        topic="Project Depth Screen: Threshold Test project",
        status="active",
        is_micro=True,
        project_id=project.id
    )
    db_session.add(session_a)
    db_session.flush()

    q_a1 = InterviewQuestion(session_id=session_a.id, topic="React", question="Q1", difficulty="hard", ai_score=6, user_answer="Answer 1")
    db_session.add(q_a1)
    db_session.commit()

    mock_gemini_resp = MagicMock()
    mock_gemini_resp.status_code = 200
    mock_gemini_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": '{"technical_score": 6, "communication_score": 6, "verdict": "Adequate", "feedback": "Okay", "mistakes": [], "improvement": "None", "model_answer": "Model", "depth_verified_recommendation": true}'
                        }
                    ]
                }
            }
        ]
    }
    mock_gemini_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_gemini_resp)

    with patch("app.modules.interview.service.settings.GEMINI_API_KEY", "test"), \
         patch("app.modules.interview.service.httpx.AsyncClient") as mock_class:
        mock_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_class.return_value.__aexit__ = AsyncMock(return_value=False)

        await interview_service.evaluate_single_answer_async(
            db_session,
            user_id=sample_user.id,
            session_id=session_a.id,
            question_id=q_a1.id,
            user_answer="Answer 1"
        )

    db_session.refresh(project)
    assert project.depth_verified is True
    assert project.depth_verified_at is not None

    # Reset project and Scenario B: overall_score < 6 but depth_verified_recommendation is True => False
    project.depth_verified = False
    project.depth_verified_at = None
    db_session.commit()

    session_b = InterviewSession(
        user_id=sample_user.id,
        branch="CSE",
        topic="Project Depth Screen: Threshold Test project",
        status="active",
        is_micro=True,
        project_id=project.id
    )
    db_session.add(session_b)
    db_session.flush()

    q_b1 = InterviewQuestion(session_id=session_b.id, topic="React", question="Q1", difficulty="hard", ai_score=5, user_answer="Answer 1")
    db_session.add(q_b1)
    db_session.commit()

    mock_gemini_resp_b = MagicMock()
    mock_gemini_resp_b.status_code = 200
    mock_gemini_resp_b.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": '{"technical_score": 5, "communication_score": 6, "verdict": "Adequate", "feedback": "Okay", "mistakes": [], "improvement": "None", "model_answer": "Model", "depth_verified_recommendation": true}'
                        }
                    ]
                }
            }
        ]
    }
    mock_gemini_resp_b.raise_for_status = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_gemini_resp_b)

    with patch("app.modules.interview.service.settings.GEMINI_API_KEY", "test"), \
         patch("app.modules.interview.service.httpx.AsyncClient") as mock_class:
        mock_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_class.return_value.__aexit__ = AsyncMock(return_value=False)

        await interview_service.evaluate_single_answer_async(
            db_session,
            user_id=sample_user.id,
            session_id=session_b.id,
            question_id=q_b1.id,
            user_answer="Answer 1"
        )

    db_session.refresh(project)
    assert project.depth_verified is False

    # Scenario C: overall_score >= 6 but depth_verified_recommendation is False => False
    project.depth_verified = False
    project.depth_verified_at = None
    db_session.commit()

    session_c = InterviewSession(
        user_id=sample_user.id,
        branch="CSE",
        topic="Project Depth Screen: Threshold Test project",
        status="active",
        is_micro=True,
        project_id=project.id
    )
    db_session.add(session_c)
    db_session.flush()

    q_c1 = InterviewQuestion(session_id=session_c.id, topic="React", question="Q1", difficulty="hard", ai_score=8, user_answer="Answer 1")
    db_session.add(q_c1)
    db_session.commit()

    mock_gemini_resp_c = MagicMock()
    mock_gemini_resp_c.status_code = 200
    mock_gemini_resp_c.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": '{"technical_score": 8, "communication_score": 6, "verdict": "Strong", "feedback": "Okay", "mistakes": [], "improvement": "None", "model_answer": "Model", "depth_verified_recommendation": false}'
                        }
                    ]
                }
            }
        ]
    }
    mock_gemini_resp_c.raise_for_status = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_gemini_resp_c)

    with patch("app.modules.interview.service.settings.GEMINI_API_KEY", "test"), \
         patch("app.modules.interview.service.httpx.AsyncClient") as mock_class:
        mock_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_class.return_value.__aexit__ = AsyncMock(return_value=False)

        await interview_service.evaluate_single_answer_async(
            db_session,
            user_id=sample_user.id,
            session_id=session_c.id,
            question_id=q_c1.id,
            user_answer="Answer 1"
        )

    db_session.refresh(project)
    assert project.depth_verified is False
