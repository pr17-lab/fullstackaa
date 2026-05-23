"""
Integration tests for Roadmap Task Tracking and Link Ingestion Pipeline.
"""
import uuid
import pytest
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch

from app.models.roadmap import Roadmap, RoadmapTask
from app.models.skill_taxonomy import SkillTaxonomy
from app.models.student_skill import StudentSkill


@pytest.fixture
def sample_roadmap_and_tasks(db_session, sample_user):
    """Fixture to seed a sample active roadmap and tasks."""
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
        db_session.refresh(skill)

    roadmap = Roadmap(
        id=uuid.uuid4(),
        user_id=sample_user.id,
        job_role="Backend Engineer",
        status="active",
        total_tasks=3,
        completed_tasks=0
    )
    db_session.add(roadmap)
    db_session.commit()

    task_learn = RoadmapTask(
        id=uuid.uuid4(),
        roadmap_id=roadmap.id,
        skill_id=skill.id,
        associated_skill_id=skill.id,
        phase="learn",
        task_type="learn",
        title="Learn FastAPI",
        estimated_hours=5,
        order_index=1,
        status="pending"
    )

    task_apply = RoadmapTask(
        id=uuid.uuid4(),
        roadmap_id=roadmap.id,
        skill_id=skill.id,
        associated_skill_id=skill.id,
        phase="apply",
        task_type="apply",
        title="Apply FastAPI",
        estimated_hours=12,
        order_index=3,
        status="pending"
    )

    db_session.add_all([task_learn, task_apply])
    db_session.commit()
    db_session.refresh(task_learn)
    db_session.refresh(task_apply)

    return roadmap, task_learn, task_apply, skill


def test_complete_task_unauthorized(client):
    """Test that unauthorized requests are rejected."""
    task_id = uuid.uuid4()
    response = client.post(f"/api/roadmap/tasks/{task_id}/complete", json={})
    assert response.status_code == 401


def test_complete_non_existent_task(auth_client):
    """Test that completing a non-existent task returns 404."""
    task_id = uuid.uuid4()
    response = auth_client.post(f"/api/roadmap/tasks/{task_id}/complete", json={})
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_complete_standard_task(auth_client, db_session, sample_roadmap_and_tasks):
    """Test that completing a standard task updates it to completed immediately."""
    _, task_learn, _, _ = sample_roadmap_and_tasks

    response = auth_client.post(
        f"/api/roadmap/tasks/{task_learn.id}/complete",
        json={"feedback_score": 5}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Verify db state
    db_session.refresh(task_learn)
    assert task_learn.status == "completed"
    assert task_learn.completed_at is not None
    assert task_learn.feedback_score == 5


def test_complete_apply_task_missing_link(auth_client, sample_roadmap_and_tasks):
    """Test that apply tasks require a submission link."""
    _, _, task_apply, _ = sample_roadmap_and_tasks

    response = auth_client.post(
        f"/api/roadmap/tasks/{task_apply.id}/complete",
        json={}
    )
    assert response.status_code == 400
    assert "Submission link is required" in response.json()["detail"]


def test_complete_apply_task_invalid_link(auth_client, sample_roadmap_and_tasks):
    """Test that apply tasks require a valid GitHub repository link."""
    _, _, task_apply, _ = sample_roadmap_and_tasks

    response = auth_client.post(
        f"/api/roadmap/tasks/{task_apply.id}/complete",
        json={"submission_link": "https://gitlab.com/test-repo"}
    )
    assert response.status_code == 400
    assert "repo_url must contain github.com" in response.json()["detail"]


def test_complete_apply_task_queues_successfully(auth_client, db_session, sample_roadmap_and_tasks):
    """Test that valid GitHub links for apply tasks transition status to pending validation and queue processing."""
    _, _, task_apply, _ = sample_roadmap_and_tasks

    # Mock the background task execution
    with patch("app.modules.roadmap.router.verify_github_complexity_async") as mock_verify:
        response = auth_client.post(
            f"/api/roadmap/tasks/{task_apply.id}/complete",
            json={"submission_link": "https://github.com/test/repo"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert "Project submission queued" in data["message"]
        
        # Verify background task is triggered
        mock_verify.assert_called_once()

        # Verify db state changes
        db_session.refresh(task_apply)
        assert task_apply.validation_status == "pending"
        assert task_apply.submission_link == "https://github.com/test/repo"
        assert task_apply.status == "pending"  # remains pending until verified


@pytest.mark.asyncio
async def test_verify_github_complexity_async_success_updates_task(db_session, sample_user, sample_roadmap_and_tasks):
    """Test that a successful verification updates task validation_status to verified, task to completed, and triggers calibration."""
    from app.modules.skills.project_service import verify_github_complexity_async
    
    roadmap, _, task_apply, skill = sample_roadmap_and_tasks

    # Mock API responses for successful check
    mock_repo_resp = MagicMock()
    mock_repo_resp.status_code = 200
    mock_repo_resp.json.return_value = {"description": "FastAPI App"}

    mock_commits_resp = MagicMock()
    mock_commits_resp.status_code = 200
    mock_commits_resp.json.return_value = [{"sha": f"sha{i}"} for i in range(15)]

    mock_contents_resp = MagicMock()
    mock_contents_resp.status_code = 200
    mock_contents_resp.json.return_value = [{"name": "conftest.py"}]

    mock_readme_resp = MagicMock()
    mock_readme_resp.status_code = 200
    mock_readme_resp.json.return_value = {"content": "dGVzdCByZWFkbWU="}  # 'test readme' in base64

    mock_gemini_resp = MagicMock()
    mock_gemini_resp.status_code = 200
    mock_gemini_resp.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "[\"FastAPI\"]"}]}}]
    }
    mock_gemini_resp.raise_for_status = MagicMock()

    async def mock_get(url, headers=None):
        if "/commits" in url:
            return mock_commits_resp
        elif "/contents" in url:
            return mock_contents_resp
        elif "/readme" in url:
            return mock_readme_resp
        else:
            return mock_repo_resp

    async def mock_post(url, json=None):
        return mock_gemini_resp

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=mock_get)
    mock_client.post = AsyncMock(side_effect=mock_post)

    with patch("app.modules.skills.project_service.settings.GEMINI_API_KEY", "test"), \
         patch("app.modules.skills.project_service.httpx.AsyncClient") as mock_class:
        mock_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_class.return_value.__aexit__ = AsyncMock(return_value=False)

        await verify_github_complexity_async(
            repo_url="https://github.com/student/fastapi-app",
            user_id=sample_user.id,
            db=db_session,
            task_id=task_apply.id
        )

    # Verify db state updates
    db_session.refresh(task_apply)
    assert task_apply.validation_status == "verified"
    assert task_apply.status == "completed"
    assert task_apply.completed_at is not None

    db_session.refresh(roadmap)
    assert roadmap.completed_tasks == 1

    # Verify StudentSkill score is calibrated
    ss = db_session.query(StudentSkill).filter(
        StudentSkill.user_id == sample_user.id,
        StudentSkill.skill_id == skill.id
    ).first()
    assert ss is not None
    # Complexity: 20 (base) + 10 (commits) + 15 (architecture/conftest.py) + 0 (readme) = 45 points
    assert float(ss.project_weight) == 45.0


@pytest.mark.asyncio
async def test_verify_github_complexity_async_failure_updates_task(db_session, sample_user, sample_roadmap_and_tasks):
    """Test that a failed base repository check sets validation_status to failed and keeps status pending."""
    from app.modules.skills.project_service import verify_github_complexity_async
    
    roadmap, _, task_apply, _ = sample_roadmap_and_tasks

    # Mock API response for non-existent repo (404)
    mock_repo_resp = MagicMock()
    mock_repo_resp.status_code = 404

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_repo_resp)

    with patch("app.modules.skills.project_service.httpx.AsyncClient") as mock_class:
        mock_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_class.return_value.__aexit__ = AsyncMock(return_value=False)

        await verify_github_complexity_async(
            repo_url="https://github.com/student/nonexistent-app",
            user_id=sample_user.id,
            db=db_session,
            task_id=task_apply.id
        )

    # Verify db state updates
    db_session.refresh(task_apply)
    assert task_apply.validation_status == "failed"
    assert task_apply.status == "pending"

    db_session.refresh(roadmap)
    assert roadmap.completed_tasks == 0
