import uuid
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.models.interview import InterviewSession, InterviewQuestion
from app.models.skill_taxonomy import SkillTaxonomy
from app.models.roadmap import Roadmap, RoadmapTask
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

def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_get_practice_topics(auth_client, db_session, sample_user):
    # Seed skill taxonomy
    _get_or_create_skill(db_session, "Machine Learning", "ml", "concept")
    _get_or_create_skill(db_session, "FastAPI", "backend", "tool")

    response = auth_client.get("/api/skills/topics")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    names = [s["skill_name"] for s in data]
    assert "Machine Learning" in names
    assert "FastAPI" in names


@pytest.mark.asyncio
async def test_create_practice_topic_session(auth_client, db_session, sample_user, sample_student_profile):
    skill = _get_or_create_skill(db_session, "SQL", "database", "tool")

    mock_gemini_resp = MagicMock()
    mock_gemini_resp.status_code = 200
    mock_gemini_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": '{"questions": [{"topic": "SQL", "question": "Q1", "difficulty": "hard"}, {"topic": "SQL", "question": "Q2", "difficulty": "hard"}, {"topic": "SQL", "question": "Q3", "difficulty": "hard"}]}'
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
         patch("app.modules.interview.service.settings.GROQ_API_KEY", None), \
         patch("app.modules.interview.service.httpx.AsyncClient") as mock_class:
        mock_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_class.return_value.__aexit__ = AsyncMock(return_value=False)

        response = auth_client.post(
            "/api/interview/sessions/practice-topic",
            json={
                "skill_id": str(skill.id),
                "limit": 3
            }
        )

    assert response.status_code == 201
    data = response.json()
    assert data["associated_skill_id"] == str(skill.id)
    assert data["is_micro"] is True
    assert data["topic"] == "Practice Interview: SQL"
    assert len(data["questions"]) == 3


@pytest.mark.asyncio
async def test_complete_practice_topic_session(db_session, sample_user, sample_student_profile):
    is_sqlite = db_session.bind.dialect.name == "sqlite"
    skill = _get_or_create_skill(db_session, "SQL", "database", "tool")

    session = InterviewSession(
        user_id=sample_user.id,
        branch="CSE",
        topic="Practice Interview: SQL",
        status="active",
        is_micro=True,
        associated_skill_id=skill.id
    )
    db_session.add(session)
    db_session.flush()

    q1 = InterviewQuestion(session_id=session.id, topic="SQL", question="Q1", difficulty="hard", ai_score=8, user_answer="Answer 1")
    q2 = InterviewQuestion(session_id=session.id, topic="SQL", question="Q2", difficulty="hard", ai_score=7, user_answer="Answer 2")
    q3 = InterviewQuestion(session_id=session.id, topic="SQL", question="Q3", difficulty="hard", user_answer="Answer 3")
    db_session.add_all([q1, q2, q3])
    db_session.commit()

    # Pre-seed StudentSkill
    ss = StudentSkill(
        user_id=sample_user.id,
        skill_id=skill.id,
        resume_weight=50.0,
        project_weight=0.0,
        interview_weight=0.0,
        communication_weight=0.0,
        source=None if is_sqlite else ["resume"]
    )
    db_session.add(ss)
    db_session.commit()

    mock_gemini_resp = MagicMock()
    mock_gemini_resp.status_code = 200
    mock_gemini_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": '{"technical_score": 8, "communication_score": 8, "verdict": "Strong", "feedback": "Good", "mistakes": [], "improvement": "None", "model_answer": "Model"}'
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

    db_session.refresh(ss)
    assert float(ss.interview_weight) == 10.0
    if not is_sqlite:
        assert "interview" in ss.source


@pytest.mark.asyncio
async def test_practice_topic_satisfies_gating(auth_client, db_session, sample_user, sample_student_profile):
    is_sqlite = db_session.bind.dialect.name == "sqlite"
    skill = _get_or_create_skill(db_session, "SQL", "database", "tool")

    # Seed Roadmap with a practice task and an apply task
    roadmap = Roadmap(
        id=uuid.uuid4(),
        user_id=sample_user.id,
        job_role="Data Engineer",
        status="active",
        total_tasks=2,
        completed_tasks=0
    )
    db_session.add(roadmap)
    db_session.commit()

    task_practice = RoadmapTask(
        id=uuid.uuid4(),
        roadmap_id=roadmap.id,
        skill_id=skill.id,
        associated_skill_id=skill.id,
        phase="practice",
        task_type="practice",
        title="Practice interview",
        status="pending"
    )
    task_apply = RoadmapTask(
        id=uuid.uuid4(),
        roadmap_id=roadmap.id,
        skill_id=skill.id,
        associated_skill_id=skill.id,
        phase="apply",
        task_type="apply",
        title="Build SQL schema",
        status="pending"
    )
    db_session.add_all([task_practice, task_apply])
    db_session.commit()

    # Verify that completing the apply task directly fails initially with 409 Conflict
    response = auth_client.post(
        f"/api/roadmap/tasks/{task_apply.id}/complete",
        json={"submission_link": "https://github.com/test/repo", "feedback_score": 5}
    )
    assert response.status_code == 409
    assert "Complete the Learn/Practice steps" in response.json()["detail"]

    # Now create and complete a completed practice interview covering the same skill
    session = InterviewSession(
        user_id=sample_user.id,
        branch="CSE",
        topic="Practice Interview: SQL",
        status="completed",
        is_micro=True,
        associated_skill_id=skill.id
    )
    db_session.add(session)
    db_session.flush()

    q1 = InterviewQuestion(session_id=session.id, topic="SQL", question="Q1", difficulty="hard", ai_score=8, user_answer="A1")
    q2 = InterviewQuestion(session_id=session.id, topic="SQL", question="Q2", difficulty="hard", ai_score=7, user_answer="A2")
    q3 = InterviewQuestion(session_id=session.id, topic="SQL", question="Q3", difficulty="hard", ai_score=8, user_answer="A3")
    db_session.add_all([q1, q2, q3])
    db_session.commit()

    # Now attempting to complete the apply task should succeed, because SQL practice phase gating is satisfied
    # and it should auto-complete the sibling task.
    with patch("app.modules.roadmap.router.verify_github_complexity_async") as mock_verify:
        response = auth_client.post(
            f"/api/roadmap/tasks/{task_apply.id}/complete",
            json={"submission_link": "https://github.com/test/repo", "feedback_score": 5}
        )
        assert response.status_code == 200

    db_session.refresh(task_practice)
    assert task_practice.status == "completed"


@pytest.mark.asyncio
async def test_practice_topic_low_score_gate_message(auth_client, db_session, sample_user, sample_student_profile):
    skill = _get_or_create_skill(db_session, "Django", "web", "tool")

    roadmap = Roadmap(
        id=uuid.uuid4(),
        user_id=sample_user.id,
        job_role="Backend Developer",
        status="active",
        total_tasks=2,
        completed_tasks=0
    )
    db_session.add(roadmap)
    db_session.commit()

    task_practice = RoadmapTask(
        id=uuid.uuid4(),
        roadmap_id=roadmap.id,
        skill_id=skill.id,
        associated_skill_id=skill.id,
        phase="practice",
        task_type="practice",
        title="Practice interview",
        status="pending"
    )
    task_apply = RoadmapTask(
        id=uuid.uuid4(),
        roadmap_id=roadmap.id,
        skill_id=skill.id,
        associated_skill_id=skill.id,
        phase="apply",
        task_type="apply",
        title="Build Django app",
        status="pending"
    )
    db_session.add_all([task_practice, task_apply])
    db_session.commit()

    # Create low-scoring practice session (average score 5.0)
    session = InterviewSession(
        user_id=sample_user.id,
        branch="CSE",
        topic="Practice Interview: Django",
        status="completed",
        is_micro=True,
        associated_skill_id=skill.id
    )
    db_session.add(session)
    db_session.flush()

    q1 = InterviewQuestion(session_id=session.id, topic="Django", question="Q1", difficulty="hard", ai_score=5, user_answer="A1")
    q2 = InterviewQuestion(session_id=session.id, topic="Django", question="Q2", difficulty="hard", ai_score=5, user_answer="A2")
    db_session.add_all([q1, q2])
    db_session.commit()

    # Attempt to complete the apply task, should fail with detailed 409 error
    response = auth_client.post(
        f"/api/roadmap/tasks/{task_apply.id}/complete",
        json={"submission_link": "https://github.com/test/repo", "feedback_score": 5}
    )
    assert response.status_code == 409
    assert "scored 5.0/10 on this practice interview" in response.json()["detail"]
    assert "Score 7+ to unlock" in response.json()["detail"]


@pytest.mark.asyncio
async def test_practice_topic_independent_session_unblocks(auth_client, db_session, sample_user, sample_student_profile):
    skill = _get_or_create_skill(db_session, "Flask", "web", "tool")

    roadmap = Roadmap(
        id=uuid.uuid4(),
        user_id=sample_user.id,
        job_role="Backend Developer",
        status="active",
        total_tasks=2,
        completed_tasks=0
    )
    db_session.add(roadmap)
    db_session.commit()

    task_practice = RoadmapTask(
        id=uuid.uuid4(),
        roadmap_id=roadmap.id,
        skill_id=skill.id,
        associated_skill_id=skill.id,
        phase="practice",
        task_type="practice",
        title="Practice interview",
        status="pending"
    )
    task_apply = RoadmapTask(
        id=uuid.uuid4(),
        roadmap_id=roadmap.id,
        skill_id=skill.id,
        associated_skill_id=skill.id,
        phase="apply",
        task_type="apply",
        title="Build Flask app",
        status="pending"
    )
    db_session.add_all([task_practice, task_apply])
    db_session.commit()

    # Create a completed practice session with high score (average 8.0) that has NO roadmap_task_id
    session = InterviewSession(
        user_id=sample_user.id,
        branch="CSE",
        topic="Topic practice: Flask",
        status="completed",
        is_micro=True,
        associated_skill_id=skill.id
    )
    db_session.add(session)
    db_session.flush()

    q1 = InterviewQuestion(session_id=session.id, topic="Flask", question="Q1", difficulty="hard", ai_score=8, user_answer="A1")
    q2 = InterviewQuestion(session_id=session.id, topic="Flask", question="Q2", difficulty="hard", ai_score=8, user_answer="A2")
    db_session.add_all([q1, q2])
    db_session.commit()

    # Attempting to complete the apply task should succeed, because SQL practice phase gating is satisfied
    # and it should auto-complete the sibling task.
    with patch("app.modules.roadmap.router.verify_github_complexity_async") as mock_verify:
        response = auth_client.post(
            f"/api/roadmap/tasks/{task_apply.id}/complete",
            json={"submission_link": "https://github.com/test/repo", "feedback_score": 5}
        )
        assert response.status_code == 200

    db_session.refresh(task_practice)
    assert task_practice.status == "completed"
