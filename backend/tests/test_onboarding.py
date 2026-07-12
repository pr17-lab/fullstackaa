import uuid
import pytest
from unittest.mock import MagicMock, patch
from app.models.skill_taxonomy import SkillTaxonomy
from app.models.student_skill import StudentSkill
from app.models.roadmap import Roadmap, RoadmapTask
from app.models.student_preference import StudentPreference
from app.modules.skills.engine import calculate_composite_score

def test_calculate_composite_score_fallback():
    # 1. Fallback formula: (resume_weight * 0.2 + project_weight * 0.4) / 0.6
    # resume_weight = 70.0, project_weight = 0.0, is_interview_scored = False
    score_unscored = calculate_composite_score(resume=70.0, project=0.0, interview=0.0, communication=0.0, is_interview_scored=False)
    # Expected: (70.0 * 0.2 + 0.0) / 0.6 = 14.0 / 0.6 = 23.33
    assert score_unscored == pytest.approx(23.33, abs=1e-2)

    # 2. Standard formula: (resume_weight * 0.2) + (project_weight * 0.4) + (interview_weight * 0.4)
    # resume_weight = 70.0, project_weight = 50.0, interview_weight = 80.0, is_interview_scored = True
    score_scored = calculate_composite_score(resume=70.0, project=50.0, interview=80.0, communication=0.0, is_interview_scored=True)
    # Expected: (70 * 0.2) + (50 * 0.4) + (80 * 0.4) = 14.0 + 20.0 + 32.0 = 66.0
    assert score_scored == 66.0

def test_api_extract_resume_skills_success(auth_client, db_session, sample_user, sample_student_profile):
    # Seed a SkillTaxonomy tool
    skill = db_session.query(SkillTaxonomy).filter(SkillTaxonomy.skill_name == "FastAPI").first()
    if not skill:
        skill = SkillTaxonomy(
            id=uuid.uuid4(),
            skill_name="FastAPI",
            category="backend",
            skill_type="tool"
        )
        db_session.add(skill)
        db_session.commit()

    # Seed student preference dialect-safely
    is_sqlite = db_session.bind.dialect.name == "sqlite"
    if is_sqlite:
        import json
        from sqlalchemy import text
        db_session.execute(
            text(
                "INSERT INTO student_preferences (id, user_id, target_roles, preferred_domains, open_to_remote, career_transition, timeline_months, experience_level, onboarding_step) "
                "VALUES (:id, :user_id, :target_roles, :preferred_domains, 1, 0, 6, 'fresher', 'preferred_role_set')"
            ),
            {
                "id": uuid.uuid4().hex,
                "user_id": sample_user.id.hex,
                "target_roles": json.dumps(["Backend Developer"]),
                "preferred_domains": json.dumps(["Software"])
            }
        )
        db_session.commit()
        pref = db_session.query(StudentPreference).filter(StudentPreference.user_id == sample_user.id).first()
    else:
        pref = StudentPreference(
            id=uuid.uuid4(),
            user_id=sample_user.id,
            target_roles=["Backend Developer"],
            preferred_domains=["Software"],
            timeline_months=6,
            experience_level="fresher",
            onboarding_step="preferred_role_set"
        )
        db_session.add(pref)
        db_session.commit()

    # Mock Gemini response to return FastAPI
    mock_gemini_resp = MagicMock()
    mock_gemini_resp.status_code = 200
    mock_gemini_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": '["FastAPI"]'
                        }
                    ]
                }
            }
        ]
    }
    
    with patch("app.core.config.settings.GEMINI_API_KEY", "test-key"), \
         patch("httpx.AsyncClient.post", return_value=mock_gemini_resp):
        
        response = auth_client.post(
            "/api/skills/extract-resume-skills",
            json={"resume_text": "I am a backend developer experienced in FastAPI framework."}
        )

        assert response.status_code == 201
        assert response.json()["success"] is True
        assert "FastAPI" in response.json()["skills_extracted"]

        # Verify StudentSkill creation and score
        ss = db_session.query(StudentSkill).filter(
            StudentSkill.user_id == sample_user.id,
            StudentSkill.skill_id == skill.id
        ).first()
        
        assert ss is not None
        assert float(ss.resume_weight) == 70.0
        # Expected: (70.0 * 0.2 + 0.0) / 0.6 = 23.33
        assert float(ss.confidence_score) == pytest.approx(23.33, abs=1e-2)
        assert ss.is_interview_scored is False

        # Verify onboarding_step is updated
        db_session.refresh(pref)
        assert pref.onboarding_step == "resume_uploaded"

def test_api_create_session_from_roadmap_task(auth_client, db_session, sample_user, sample_student_profile):
    # Seed SkillTaxonomy
    skill = db_session.query(SkillTaxonomy).filter(SkillTaxonomy.skill_name == "Docker").first()
    if not skill:
        skill = SkillTaxonomy(
            id=uuid.uuid4(),
            skill_name="Docker",
            category="devops",
            skill_type="tool",
            description="Containerization tool for deployment."
        )
        db_session.add(skill)
        db_session.commit()

    # Seed active Roadmap & Task
    roadmap = Roadmap(
        id=uuid.uuid4(),
        user_id=sample_user.id,
        job_role="DevOps Engineer",
        status="active",
        total_tasks=1,
        completed_tasks=0
    )
    db_session.add(roadmap)
    db_session.commit()

    task = RoadmapTask(
        id=uuid.uuid4(),
        roadmap_id=roadmap.id,
        skill_id=skill.id,
        associated_skill_id=skill.id,
        phase="practice",
        task_type="practice",
        title="Practice Interview: Docker",
        estimated_hours=4,
        order_index=1,
        status="pending"
    )
    db_session.add(task)
    db_session.commit()

    # Create interview session seeding from task
    with patch("app.modules.interview.service.settings.GROQ_API_KEY", "mock-groq-key"), \
         patch("app.modules.interview.service.InterviewService.generate_questions_async", return_value=([
             {"question": "What is a Docker container?", "topic": "Docker", "difficulty": "medium"},
             {"question": "How do you optimize a Dockerfile?", "topic": "Docker", "difficulty": "medium"}
         ], "mock")):
        
        response = auth_client.post(
            "/api/interview/sessions",
            json={
                "jd_text": "",
                "resume_context": "Docker user",
                "limit": 2,
                "roadmap_task_id": str(task.id)
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["roadmap_task_id"] == str(task.id)
        assert data["associated_skill_id"] == str(skill.id)
        assert data["is_micro"] is True
        assert data["topic"] == "Practice Interview: Docker"
