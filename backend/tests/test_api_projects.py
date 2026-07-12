"""
Integration tests for GitHub project verification endpoint and model validation.
"""
import pytest
from app.models.student_project import StudentProject

def test_verify_project_unauthorized(client):
    """Test that unauthorized requests are rejected."""
    response = client.post(
        "/api/skills/project/verify",
        json={"repo_url": "https://github.com/test/repo"}
    )
    assert response.status_code == 401


def test_verify_project_invalid_url(auth_client):
    """Test that invalid domains are rejected with validation error (422)."""
    response = auth_client.post(
        "/api/skills/project/verify",
        json={"repo_url": "https://gitlab.com/test/repo"}
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert "github.com" in data["detail"][0]["msg"]


def test_verify_project_success(auth_client):
    """Test that valid github.com URLs are queued successfully (202)."""
    response = auth_client.post(
        "/api/skills/project/verify",
        json={"repo_url": "https://github.com/student/sata-platform"}
    )
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "processing"
    assert "Repository analysis queued" in data["message"]


def test_student_project_model_validation(db_session, sample_user):
    """Test Python-level validates domain checks on the StudentProject model."""
    # Attempting to assign a non-github repo url should raise ValueError immediately
    with pytest.raises(ValueError) as exc:
        StudentProject(
            user_id=sample_user.id,
            title="Invalid Test Project",
            repo_url="https://bitbucket.org/student/repo"
        )
    assert "must be a github.com link" in str(exc.value)

    # Saving a valid github repo url should succeed
    valid_project = StudentProject(
        user_id=sample_user.id,
        title="Valid Test Project",
        repo_url="https://github.com/student/repo"
    )
    db_session.add(valid_project)
    db_session.commit()
    
    assert valid_project.id is not None
    assert valid_project.repo_url == "https://github.com/student/repo"


@pytest.mark.asyncio
async def test_verify_github_complexity_async_processing(db_session, sample_user):
    """Test full verify_github_complexity_async math, scoring, Gemini integration, and persistence."""
    from app.modules.skills.project_service import verify_github_complexity_async
    from app.models.student_project import StudentProject
    from app.models.skill_taxonomy import SkillTaxonomy
    from app.models.student_skill import StudentSkill
    from unittest.mock import MagicMock, AsyncMock, patch
    import base64
    import json

    # Seed SkillTaxonomy entries FastAPI, React, and Docker for validation sync
    for name in ["FastAPI", "React", "Docker"]:
        tax = (
            db_session.query(SkillTaxonomy)
            .filter(SkillTaxonomy.skill_name == name)
            .first()
        )
        if not tax:
            tax = SkillTaxonomy(
                skill_name=name,
                category="backend" if name != "React" else "frontend",
                skill_type="tool"
            )
            db_session.add(tax)
    db_session.commit()

    # Mock response definitions
    mock_repo_resp = MagicMock()
    mock_repo_resp.status_code = 200
    mock_repo_resp.json.return_value = {"description": "SATA B.Tech Career Intelligence Platform"}

    # 35 commits (score multiplier = 20 points)
    mock_commits_resp = MagicMock()
    mock_commits_resp.status_code = 200
    mock_commits_resp.json.return_value = [{"sha": f"sha{i}"} for i in range(35)]

    # Contents tree with DevOps, Testing, and Boundaries (all three: 15 + 15 + 10 = 40 points)
    mock_contents_resp = MagicMock()
    mock_contents_resp.status_code = 200
    mock_contents_resp.json.return_value = [
        {"name": "Dockerfile", "type": "file"},
        {"name": "conftest.py", "type": "file"},
        {"name": "middleware", "type": "dir"},
    ]

    # README content: 2500 characters (documentation multiplier = 20 points)
    readme_text = "A" * 2500
    readme_b64 = base64.b64encode(readme_text.encode("utf-8")).decode("utf-8")
    
    mock_readme_resp = MagicMock()
    mock_readme_resp.status_code = 200
    mock_readme_resp.json.return_value = {"content": readme_b64}

    # Gemini 1.5 Flash extraction
    mock_gemini_resp = MagicMock()
    mock_gemini_resp.status_code = 200
    mock_gemini_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps(["FastAPI", "React", "Docker"])
                        }
                    ]
                }
            }
        ]
    }
    mock_gemini_resp.raise_for_status = MagicMock()

    # AsyncClient post/get dispatcher
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
            repo_url="https://github.com/student/sata-platform",
            user_id=sample_user.id,
            db=db_session
        )

    # Assert persistence
    project = (
        db_session.query(StudentProject)
        .filter(
            StudentProject.user_id == sample_user.id,
            StudentProject.repo_url == "https://github.com/student/sata-platform"
        )
        .first()
    )
    
    assert project is not None
    assert project.calculated_complexity == 100  # 20 (base) + 20 (commits) + 40 (architecture) + 20 (README)
    assert project.extracted_skills == ["FastAPI", "React", "Docker"]
    if db_session.bind.dialect.name != "sqlite":
        assert project.tech_stack == ["FastAPI", "React", "Docker"]
    assert project.domain == "GitHub Integration"
    assert project.description == "SATA B.Tech Career Intelligence Platform"
    assert project.analyzed_at is not None

    # Assert StudentSkills synchronization & calibration
    skills = db_session.query(StudentSkill).filter(StudentSkill.user_id == sample_user.id).all()
    assert len(skills) == 3
    
    skill_names = {s.skill.skill_name for s in skills}
    assert skill_names == {"FastAPI", "React", "Docker"}
    
    for s in skills:
        assert float(s.project_weight) == 100.0
        # Formula (fallback): (resume_weight * 0.2 + project_weight * 0.4) / 0.6
        # Since it's a new row, resume_weight = 0.0, so:
        # confidence_score = (0.0 * 0.2 + 100.0 * 0.4) / 0.6 = 66.67
        assert float(s.confidence_score) == pytest.approx(66.67, abs=1e-2)
        assert s.level == "moderate"  # 66.67 is >= 50 and < 80
        if db_session.bind.dialect.name != "sqlite":
            assert "project" in s.source


@pytest.mark.asyncio
async def test_verify_github_complexity_async_existing_skill(db_session, sample_user):
    """Test verify_github_complexity_async updates an existing StudentSkill and recalculates score correctly."""
    from app.modules.skills.project_service import verify_github_complexity_async
    from app.models.student_project import StudentProject
    from app.models.skill_taxonomy import SkillTaxonomy
    from app.models.student_skill import StudentSkill
    from unittest.mock import MagicMock, AsyncMock, patch
    import base64
    import json

    # 1. Seed SkillTaxonomy
    tax = (
        db_session.query(SkillTaxonomy)
        .filter(SkillTaxonomy.skill_name == "FastAPI")
        .first()
    )
    if not tax:
        tax = SkillTaxonomy(
            skill_name="FastAPI",
            category="backend",
            skill_type="tool"
        )
        db_session.add(tax)
        db_session.commit()
        db_session.refresh(tax)

    # 2. Seed existing StudentSkill with weights
    ss = (
        db_session.query(StudentSkill)
        .filter(
            StudentSkill.user_id == sample_user.id,
            StudentSkill.skill_id == tax.id
        )
        .first()
    )
    if ss:
        db_session.delete(ss)
        db_session.commit()

    is_sqlite = db_session.bind.dialect.name == "sqlite"
    ss = StudentSkill(
        user_id=sample_user.id,
        skill_id=tax.id,
        resume_weight=50.0,
        project_weight=0.0,
        interview_weight=80.0,
        is_interview_scored=True,
        source=["resume", "interview"] if not is_sqlite else None
    )
    db_session.add(ss)
    db_session.commit()

    # Mocks
    mock_repo_resp = MagicMock()
    mock_repo_resp.status_code = 200
    mock_repo_resp.json.return_value = {"description": "FastAPI Project"}

    mock_commits_resp = MagicMock()
    mock_commits_resp.status_code = 200
    # 5 commits (+5 points)
    mock_commits_resp.json.return_value = [{"sha": f"sha{i}"} for i in range(5)]

    # Contents tree - empty (+0 points)
    mock_contents_resp = MagicMock()
    mock_contents_resp.status_code = 200
    mock_contents_resp.json.return_value = []

    # README content: 600 characters (documentation multiplier = 10 points)
    readme_text = "A" * 600
    readme_b64 = base64.b64encode(readme_text.encode("utf-8")).decode("utf-8")
    
    mock_readme_resp = MagicMock()
    mock_readme_resp.status_code = 200
    mock_readme_resp.json.return_value = {"content": readme_b64}

    # Gemini 1.5 Flash extraction
    mock_gemini_resp = MagicMock()
    mock_gemini_resp.status_code = 200
    mock_gemini_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps(["FastAPI"])
                        }
                    ]
                }
            }
        ]
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
            db=db_session
        )

    # Complexity score: 20 (base) + 5 (commits) + 10 (README) = 35
    # Assert existing StudentSkill has been updated
    db_session.refresh(ss)
    assert float(ss.project_weight) == 35.0
    if not is_sqlite:
        assert "project" in ss.source
    # Formula: (resume_weight * 0.2) + (project_weight * 0.4) + (interview_weight * 0.4)
    # (50.0 * 0.2) + (35.0 * 0.4) + (80.0 * 0.4) = 10.0 + 14.0 + 32.0 = 56.0
    assert float(ss.confidence_score) == 56.0
    assert ss.level == "moderate"  # 52.0 is >= 50 and < 80


def test_get_my_projects(auth_client, db_session, sample_user):
    """Test retrieving user's student projects."""
    from app.models.student_project import StudentProject
    import uuid
    
    project1 = StudentProject(
        id=uuid.uuid4(),
        user_id=sample_user.id,
        title="Project 1",
        repo_url="https://github.com/student/p1",
        depth_verified=False
    )
    db_session.add(project1)
    db_session.commit()

    response = auth_client.get("/api/skills/project")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    titles = [p["title"] for p in data]
    assert "Project 1" in titles

