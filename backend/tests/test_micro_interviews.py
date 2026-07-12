"""
Integration tests for target-scoped micro-interview initializer and task verification calibration.
"""
import uuid
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from app.models.interview import InterviewSession, InterviewQuestion
from app.models.skill_taxonomy import SkillTaxonomy
from app.models.roadmap import Roadmap, RoadmapTask
from app.models.student_skill import StudentSkill
from app.modules.interview.service import create_micro_interview_session, interview_service


@pytest.fixture
def sample_skill_and_roadmap(db_session, sample_user, sample_student_profile):
    """Fixture to seed a SkillTaxonomy tool and a Roadmap with an apply phase task."""
    skill = db_session.query(SkillTaxonomy).filter(SkillTaxonomy.skill_name == "React").first()
    if not skill:
        skill = SkillTaxonomy(
            id=uuid.uuid4(),
            skill_name="React",
            category="frontend",
            skill_type="tool"
        )
        db_session.add(skill)
        db_session.commit()
        db_session.refresh(skill)

    roadmap = Roadmap(
        id=uuid.uuid4(),
        user_id=sample_user.id,
        job_role="Frontend Engineer",
        status="active",
        total_tasks=3,
        completed_tasks=0
    )
    db_session.add(roadmap)
    db_session.commit()

    task_apply = RoadmapTask(
        id=uuid.uuid4(),
        roadmap_id=roadmap.id,
        skill_id=skill.id,
        associated_skill_id=skill.id,
        phase="apply",
        task_type="apply",
        title="Build a React app and push to GitHub",
        estimated_hours=12,
        order_index=3,
        status="pending"
    )
    db_session.add(task_apply)
    db_session.commit()
    db_session.refresh(task_apply)

    return skill, roadmap, task_apply


@pytest.mark.asyncio
async def test_create_micro_interview_session(db_session, sample_user, sample_skill_and_roadmap):
    """Test that create_micro_interview_session creates a session capped strictly at 3 questions focused on the skill."""
    skill, _, task_apply = sample_skill_and_roadmap

    # Mock Groq/Gemini calls to skip network requests
    mock_gemini_resp = MagicMock()
    mock_gemini_resp.status_code = 200
    mock_gemini_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": "{\"questions\": [{\"topic\": \"React\", \"question\": \"Q1\", \"difficulty\": \"hard\"}, {\"topic\": \"React\", \"question\": \"Q2\", \"difficulty\": \"hard\"}, {\"topic\": \"React\", \"question\": \"Q3\", \"difficulty\": \"hard\"}]}"
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

        session = await create_micro_interview_session(sample_user.id, skill.id, db_session)

    assert session is not None
    assert session.is_micro is True
    assert session.associated_skill_id == skill.id
    assert session.roadmap_task_id == task_apply.id
    assert session.topic == "Micro-Interview: React"
    assert len(session.questions) == 3
    for q in session.questions:
        assert q.topic == "React"
        assert q.difficulty == "hard"


@pytest.mark.asyncio
async def test_micro_interview_completion_calibration_success(db_session, sample_user, sample_skill_and_roadmap):
    """Test that completing a micro-interview with score >= 7 completes and verifies the RoadmapTask."""
    skill, roadmap, task_apply = sample_skill_and_roadmap

    # Create a micro-interview session with pre-scored answers
    session = InterviewSession(
        user_id=sample_user.id,
        branch="CSE",
        topic="Micro-Interview: React",
        status="active",
        is_micro=True,
        associated_skill_id=skill.id,
        roadmap_task_id=task_apply.id
    )
    db_session.add(session)
    db_session.flush()

    q1 = InterviewQuestion(session_id=session.id, topic="React", question="Q1", difficulty="hard", ai_score=8, user_answer="Answer 1")
    q2 = InterviewQuestion(session_id=session.id, topic="React", question="Q2", difficulty="hard", ai_score=7, user_answer="Answer 2")
    q3 = InterviewQuestion(session_id=session.id, topic="React", question="Q3", difficulty="hard", user_answer="Answer 3")
    db_session.add_all([q1, q2, q3])
    db_session.commit()

    # Mock the Gemini API answer evaluation response for the final question (q3) with score 8 (average becomes 7.6)
    mock_gemini_resp = MagicMock()
    mock_gemini_resp.status_code = 200
    mock_gemini_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": "{\"technical_score\": 8, \"communication_score\": 8, \"verdict\": \"Strong\", \"feedback\": \"Good\", \"mistakes\": [], \"improvement\": \"None\", \"model_answer\": \"Model\"}"
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

        result = await interview_service.evaluate_single_answer_async(
            db_session,
            user_id=sample_user.id,
            session_id=session.id,
            question_id=q3.id,
            user_answer="Answer 3"
        )

    # Verify response contains the score
    assert result["technical_score"] == 8
    
    # Verify RoadmapTask is complete & verified
    db_session.refresh(task_apply)
    assert task_apply.status == "completed"
    assert task_apply.validation_status == "verified"
    assert task_apply.completed_at is not None

    # Verify Roadmap completed tasks counter updated
    db_session.refresh(roadmap)
    assert roadmap.completed_tasks == 1

    # Verify StudentSkill exists & is calibrated
    ss = db_session.query(StudentSkill).filter(
        StudentSkill.user_id == sample_user.id,
        StudentSkill.skill_id == skill.id
    ).first()
    assert ss is not None
    assert float(ss.interview_weight) > 0.0


@pytest.mark.asyncio
async def test_micro_interview_completion_calibration_failure(db_session, sample_user, sample_skill_and_roadmap):
    """Test that completing a micro-interview with score < 7 does NOT complete the task."""
    skill, roadmap, task_apply = sample_skill_and_roadmap

    session = InterviewSession(
        user_id=sample_user.id,
        branch="CSE",
        topic="Micro-Interview: React",
        status="active",
        is_micro=True,
        associated_skill_id=skill.id,
        roadmap_task_id=task_apply.id
    )
    db_session.add(session)
    db_session.flush()

    q1 = InterviewQuestion(session_id=session.id, topic="React", question="Q1", difficulty="hard", ai_score=4, user_answer="Answer 1")
    q2 = InterviewQuestion(session_id=session.id, topic="React", question="Q2", difficulty="hard", ai_score=5, user_answer="Answer 2")
    q3 = InterviewQuestion(session_id=session.id, topic="React", question="Q3", difficulty="hard", user_answer="Answer 3")
    db_session.add_all([q1, q2, q3])
    db_session.commit()

    # Mock the Gemini API answer evaluation response for final question (q3) with score 5 (average becomes 4.6)
    mock_gemini_resp = MagicMock()
    mock_gemini_resp.status_code = 200
    mock_gemini_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": "{\"technical_score\": 5, \"communication_score\": 5, \"verdict\": \"Adequate\", \"feedback\": \"Adequate\", \"mistakes\": [], \"improvement\": \"None\", \"model_answer\": \"Model\"}"
                        }
                    ]
                }
            }
        ]
    }
    mock_gemini_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post = MagicMock(return_value=mock_gemini_resp)

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

    # Verify RoadmapTask is NOT complete & NOT verified
    db_session.refresh(task_apply)
    assert task_apply.status == "pending"
    assert task_apply.validation_status is None

    db_session.refresh(roadmap)
    assert roadmap.completed_tasks == 0
