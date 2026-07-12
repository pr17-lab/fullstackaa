"""
Integration tests for Career Recommendations dashboard endpoint and SkillGap JSONB formats.
"""

import pytest
from app.models.skill_gap import SkillGap
from app.models.skill_taxonomy import SkillTaxonomy
from app.models.student_skill import StudentSkill
from app.models.student_profile import StudentProfile
from app.models.student_preference import StudentPreference
from app.modules.skills.engine import compute_gaps_for_student


def test_career_recommendations_unauthorized(client):
    """Test that unauthorized requests to recommendations are rejected (401)."""
    response = client.get("/api/skills/recommendations")
    assert response.status_code == 401


def test_career_recommendations_success_and_jsonb_format(auth_client, db_session, sample_user):
    """Test successful GET /api/skills/recommendations, grouping, and SkillGap JSONB formatting."""
    # 1. Seed Student Profile and Preference
    profile = StudentProfile(
        user_id=sample_user.id,
        name="Career Test Student",
        department="CSE",
        semester=5,
        interests="Databases, Web"
    )
    db_session.add(profile)

    is_sqlite = db_session.bind.dialect.name == "sqlite"
    if is_sqlite:
        from sqlalchemy import text
        import json
        import uuid
        db_session.execute(
            text(
                "INSERT INTO student_preferences (id, user_id, target_roles, preferred_domains, open_to_remote, career_transition, timeline_months, experience_level) "
                "VALUES (:id, :user_id, :target_roles, :preferred_domains, 1, 0, 12, 'entry')"
            ),
            {
                "id": uuid.uuid4().hex,
                "user_id": sample_user.id.hex,
                "target_roles": json.dumps(["Software Engineer", "Backend Developer"]),
                "preferred_domains": json.dumps(["Web Technology", "Relational Databases"])
            }
        )
        db_session.commit()
    else:
        preference = StudentPreference(
            user_id=sample_user.id,
            target_roles=["Software Engineer", "Backend Developer"],
            preferred_domains=["Web Technology", "Relational Databases"],
            open_to_remote=True,
            career_transition=False,
            experience_level="entry"
        )
        db_session.add(preference)
        db_session.commit()

    # 2. Seed Skill Taxonomy concepts and tools
    # Concept skill (parent)
    db_parent = SkillTaxonomy(
        skill_name="Relational Databases",
        category="backend",
        skill_type="concept"
    )
    db_session.add(db_parent)
    db_session.flush()

    # Tool skill 1 (child with parent) -> for High Potential
    db_tool_hp = SkillTaxonomy(
        skill_name="PostgreSQL",
        category="backend",
        skill_type="tool",
        parent_id=db_parent.id
    )
    db_session.add(db_tool_hp)

    # Tool skill 2 (child with parent) -> for Strong (achieved threshold >= 70)
    db_tool_strong = SkillTaxonomy(
        skill_name="SQL",
        category="backend",
        skill_type="tool",
        parent_id=db_parent.id
    )
    db_session.add(db_tool_strong)

    # Tool skill 3 -> for Weak (achieved score < 70)
    db_tool_weak = SkillTaxonomy(
        skill_name="FastAPI",
        category="backend",
        skill_type="tool"
    )
    db_session.add(db_tool_weak)

    # Tool skill 4 -> for Missing (no student skill at all)
    db_tool_missing = SkillTaxonomy(
        skill_name="Docker",
        category="backend",
        skill_type="tool"
    )
    db_session.add(db_tool_missing)
    db_session.commit()

    # 3. Seed Job Skill Requirements
    # Insert job requirements directly
    from sqlalchemy import text
    db_session.execute(text("DELETE FROM job_skill_requirements"))
    db_session.commit()

    # Seed requirements for "Software Engineer"
    # PostgreSQL (must_have)
    # SQL (preferred)
    # FastAPI (nice_to_have)
    # Docker (must_have)
    db_session.execute(
        text(
            "INSERT INTO job_skill_requirements (id, job_role, skill_id, importance, min_score_required) "
            "VALUES "
            f"('{uuid_str()}', 'Software Engineer', '{db_tool_hp.id}', 'must_have', 70.0), "
            f"('{uuid_str()}', 'Software Engineer', '{db_tool_strong.id}', 'preferred', 70.0), "
            f"('{uuid_str()}', 'Software Engineer', '{db_tool_weak.id}', 'nice_to_have', 70.0), "
            f"('{uuid_str()}', 'Software Engineer', '{db_tool_missing.id}', 'must_have', 70.0)"
        )
    )
    db_session.commit()

    # 4. Seed Student Skills (confidence scores)
    # Seed parent skill with positive resume weight so the child becomes "High Potential"
    ss_parent = StudentSkill(
        user_id=sample_user.id,
        skill_id=db_parent.id,
        resume_weight=80.0,
        confidence_score=80.0,
        level="strong"
    )
    db_session.add(ss_parent)

    # Seed strong child skill with score >= 70
    ss_strong = StudentSkill(
        user_id=sample_user.id,
        skill_id=db_tool_strong.id,
        confidence_score=75.0,
        level="moderate"
    )
    db_session.add(ss_strong)

    # Seed weak child skill with score < 70
    ss_weak = StudentSkill(
        user_id=sample_user.id,
        skill_id=db_tool_weak.id,
        confidence_score=40.0,
        level="weak"
    )
    db_session.add(ss_weak)
    db_session.commit()

    # 5. Programmatically trigger compute_gaps_for_student
    compute_gaps_for_student(db_session, str(sample_user.id))

    # 6. Verify database records have the correct JSONB format shape
    gap_record = (
        db_session.query(SkillGap)
        .filter(SkillGap.user_id == sample_user.id, SkillGap.job_role == "Software Engineer")
        .first()
    )
    assert gap_record is not None
    assert gap_record.match_score > 0

    # Assert strong skill shape: [{skill_id, score}]
    assert len(gap_record.strong_skills) == 1
    assert gap_record.strong_skills[0]["skill_id"] == str(db_tool_strong.id)
    assert gap_record.strong_skills[0]["score"] == 75.0

    # Assert high potential shape: [{skill_id, parent_id}]
    assert len(gap_record.high_potential_skills) == 1
    assert gap_record.high_potential_skills[0]["skill_id"] == str(db_tool_hp.id)
    assert gap_record.high_potential_skills[0]["parent_id"] == str(db_parent.id)
    assert "parent_skill" not in gap_record.high_potential_skills[0] # Verify old key is deleted

    # Assert weak skill shape: [{skill_id, score}]
    assert len(gap_record.weak_skills) == 1
    assert gap_record.weak_skills[0]["skill_id"] == str(db_tool_weak.id)
    assert gap_record.weak_skills[0]["score"] == 40.0
    assert "required" not in gap_record.weak_skills[0] # Verify old key is deleted

    # Assert missing skill shape: [{skill_id}]
    assert len(gap_record.missing_skills) == 1
    assert gap_record.missing_skills[0]["skill_id"] == str(db_tool_missing.id)
    assert "importance" not in gap_record.missing_skills[0] # Verify old key is deleted
    assert "gap" not in gap_record.missing_skills[0] # Verify old key is deleted

    # 7. Query route GET /api/skills/recommendations
    response = auth_client.get("/api/skills/recommendations")
    assert response.status_code == 200
    data = response.json()

    # Assert clean sorted career dashboard response
    assert "recommendations" in data
    assert "tiers" in data
    assert "primary" in data["recommendations"]
    assert "alternatives" in data["recommendations"]

    tiers = data["tiers"]
    assert "excellent" in tiers
    assert "good" in tiers
    assert "potential" in tiers
    assert "low" in tiers

    # Software Engineer match_score:
    # sum_weights = 3 (PostgreSQL, hp) + 2 (SQL, strong) + 1 (FastAPI, weak) + 3 (Docker, missing) = 9
    # sum_met = 3 * 0.4 (hp, 1.2) + 2 (strong, 2) + 0 (weak, 0) + 0 (missing, 0) = 3.2
    # match_score = 3.2 / 9 * 100 = 35.55
    # Department bonus for CSE: +15 = 50.56
    assert len(tiers["good"]) == 1
    assert tiers["good"][0]["job_role"] == "Software Engineer"
    assert tiers["good"][0]["match_score"] == pytest.approx(50.56, abs=0.1)
    assert tiers["good"][0]["match_label"] == "Good"

    # Verify high potential skill is enriched with names
    hp_enriched = tiers["good"][0]["high_potential_skills"][0]
    assert hp_enriched["skill_name"] == "PostgreSQL"
    assert hp_enriched["parent_name"] == "Relational Databases"


def uuid_str() -> str:
    import uuid
    return uuid.uuid4().hex


def test_career_recommendation_breakdown_tiers(auth_client, db_session, sample_user):
    """Test GET /api/skills/recommendations/{job_role}/breakdown for all match tiers, checking distance calculation and leverage sorting."""
    # 1. Clean previous data
    from app.models.student_profile import StudentProfile
    from app.models.student_preference import StudentPreference
    from app.models.student_skill import StudentSkill
    from app.models.skill_taxonomy import SkillTaxonomy
    from sqlalchemy import text
    import json
    import uuid

    db_session.execute(text("DELETE FROM student_profiles"))
    db_session.execute(text("DELETE FROM student_preferences"))
    db_session.execute(text("DELETE FROM student_skills"))
    db_session.execute(text("DELETE FROM skill_taxonomy"))
    db_session.execute(text("DELETE FROM job_skill_requirements"))
    db_session.commit()

    # 2. Seed student profile (CSE)
    profile = StudentProfile(
        user_id=sample_user.id,
        name="Breakdown Test Student",
        department="CSE",
        semester=5,
        interests="Web"
    )
    db_session.add(profile)
    
    is_sqlite = db_session.bind.dialect.name == "sqlite"
    if is_sqlite:
        db_session.execute(
            text(
                "INSERT INTO student_preferences (id, user_id, target_roles, preferred_domains, open_to_remote, career_transition, timeline_months, experience_level) "
                "VALUES (:id, :user_id, :target_roles, :preferred_domains, 1, 0, 12, 'entry')"
            ),
            {
                "id": uuid.uuid4().hex,
                "user_id": sample_user.id.hex,
                "target_roles": json.dumps(["Software Engineer"]),
                "preferred_domains": json.dumps(["Web Technology"])
            }
        )
    else:
        preference = StudentPreference(
            user_id=sample_user.id,
            target_roles=["Software Engineer"],
            preferred_domains=["Web Technology"],
            open_to_remote=True,
            career_transition=False,
            experience_level="entry"
        )
        db_session.add(preference)
    db_session.commit()

    # Seed 3 taxonomy skills (FastAPI, React, Docker)
    t_fastapi = SkillTaxonomy(skill_name="FastAPI", category="backend", skill_type="tool")
    t_react = SkillTaxonomy(skill_name="React", category="frontend", skill_type="tool")
    t_docker = SkillTaxonomy(skill_name="Docker", category="cloud_devops", skill_type="tool")
    db_session.add_all([t_fastapi, t_react, t_docker])
    db_session.commit()
    db_session.refresh(t_fastapi)
    db_session.refresh(t_react)
    db_session.refresh(t_docker)

    # Seed job requirements for "Software Engineer"
    # FastAPI: must_have (weight = 3)
    # React: preferred (weight = 2)
    # Docker: nice_to_have (weight = 1)
    # Total requirements weight = 3 + 2 + 1 = 6.
    # Note: "Software Engineer" matches CSE dept bonus, which adds +15.
    db_session.execute(
        text(
            "INSERT INTO job_skill_requirements (id, job_role, skill_id, importance, min_score_required) "
            "VALUES "
            f"('{uuid_str()}', 'Software Engineer', '{t_fastapi.id}', 'must_have', 70.0), "
            f"('{uuid_str()}', 'Software Engineer', '{t_react.id}', 'preferred', 70.0), "
            f"('{uuid_str()}', 'Software Engineer', '{t_docker.id}', 'nice_to_have', 70.0)"
        )
    )
    db_session.commit()

    # --- TIER 1: Excellent Match (score >= 60.0) ---
    # Setup skills: FastAPI >= 70 (strong), React >= 70 (strong), Docker >= 70 (strong)
    # sum_met = 3 + 2 + 1 = 6. match_score = 6 / 6 * 100 = 100.0 + 15 (CSE bonus) = 100.0 (capped)
    s_fa = StudentSkill(user_id=sample_user.id, skill_id=t_fastapi.id, confidence_score=80.0, level="strong")
    s_re = StudentSkill(user_id=sample_user.id, skill_id=t_react.id, confidence_score=75.0, level="strong")
    s_do = StudentSkill(user_id=sample_user.id, skill_id=t_docker.id, confidence_score=90.0, level="strong")
    db_session.add_all([s_fa, s_re, s_do])
    db_session.commit()

    resp = auth_client.get("/api/skills/recommendations/Software%20Engineer/breakdown")
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_role"] == "Software Engineer"
    assert data["match_score"] == 100.0
    assert data["category"] == "Excellent Match"
    assert data["distance_to_next_tier"] is None

    # --- TIER 2: Good Match (35.0 <= score < 60.0) ---
    # Let's delete current skills and re-add for Good Match
    db_session.execute(text("DELETE FROM student_skills"))
    db_session.commit()
    # Setup skills: FastAPI has parent Web Technology (with resume_weight > 0), so it is high_potential (1.2 contribution).
    # React and Docker have no parent with resume_weight, so they are missing (0 contribution).
    # sum_met = 1.2. sum_weights = 6. match_score = 1.2 / 6 * 100 = 20.0 + 15 (CSE bonus) = 35.0.
    t_web = SkillTaxonomy(skill_name="Web Technology", category="backend", skill_type="concept")
    db_session.add(t_web)
    db_session.commit()
    db_session.refresh(t_web)
    t_fastapi.parent_id = t_web.id
    db_session.commit()

    s_web = StudentSkill(user_id=sample_user.id, skill_id=t_web.id, resume_weight=50.0, confidence_score=50.0, level="strong")
    db_session.add(s_web)
    db_session.commit()

    resp = auth_client.get("/api/skills/recommendations/Software%20Engineer/breakdown")
    assert resp.status_code == 200
    data = resp.json()
    assert data["match_score"] == 35.0
    assert data["category"] == "Good Match"
    assert data["distance_to_next_tier"] is not None
    assert data["distance_to_next_tier"]["next_category"] == "Excellent Match"
    assert data["distance_to_next_tier"]["points_needed"] == 25.0
    # Missing / weak skills in breakdown: React (weight 2, missing), Docker (weight 1, missing).
    # Sorted by weight descending: React (2), Docker (1).
    assert data["distance_to_next_tier"]["highest_leverage_skills"] == ["React", "Docker"]

    # --- TIER 3: Potential Match (20.0 <= score < 35.0) ---
    # Delete student skills and re-add for Potential Match
    db_session.execute(text("DELETE FROM student_skills"))
    db_session.commit()
    # Setup skills: FastAPI is high potential, no CSE bonus because department is ECE
    profile.department = "ECE"
    db_session.commit()
    s_web2 = StudentSkill(user_id=sample_user.id, skill_id=t_web.id, resume_weight=50.0, confidence_score=50.0, level="strong")
    db_session.add(s_web2)
    db_session.commit()

    resp = auth_client.get("/api/skills/recommendations/Software%20Engineer/breakdown")
    assert resp.status_code == 200
    data = resp.json()
    assert data["match_score"] == 20.0
    assert data["category"] == "Potential Match"
    assert data["distance_to_next_tier"]["next_category"] == "Good Match"
    assert data["distance_to_next_tier"]["points_needed"] == 15.0

    # --- TIER 4: Low Match (score < 20.0) ---
    db_session.execute(text("DELETE FROM student_skills"))
    db_session.commit()
    resp = auth_client.get("/api/skills/recommendations/Software%20Engineer/breakdown")
    assert resp.status_code == 200
    data = resp.json()
    assert data["match_score"] == 0.0
    assert data["category"] == "Low Match"
    assert data["distance_to_next_tier"]["next_category"] == "Potential Match"
    assert data["distance_to_next_tier"]["points_needed"] == 20.0
    assert data["distance_to_next_tier"]["highest_leverage_skills"] == ["FastAPI", "React", "Docker"]

    # --- CASE 5: 404 Not Found ---
    resp = auth_client.get("/api/skills/recommendations/NonexistentRole/breakdown")
    assert resp.status_code == 404


def test_career_recommendation_requirements_last_reviewed(auth_client, db_session, sample_user):
    """Test requirements_last_reviewed field in /api/skills/recommendations payload reflects the oldest date."""
    from app.models.student_profile import StudentProfile
    from app.models.student_preference import StudentPreference
    from app.models.student_skill import StudentSkill
    from app.models.skill_taxonomy import SkillTaxonomy
    from app.models.job_skill_requirement import JobSkillRequirement
    from sqlalchemy import text
    from datetime import datetime, timedelta
    import json
    import uuid

    # 1. Clean previous data
    db_session.execute(text("DELETE FROM student_profiles"))
    db_session.execute(text("DELETE FROM student_preferences"))
    db_session.execute(text("DELETE FROM student_skills"))
    db_session.execute(text("DELETE FROM skill_taxonomy"))
    db_session.execute(text("DELETE FROM job_skill_requirements"))
    db_session.commit()

    # 2. Seed student profile (CSE) and preference
    profile = StudentProfile(
        user_id=sample_user.id,
        name="Reviewed Test Student",
        department="CSE",
        semester=5,
        interests="Web"
    )
    db_session.add(profile)
    
    is_sqlite = db_session.bind.dialect.name == "sqlite"
    if is_sqlite:
        db_session.execute(
            text(
                "INSERT INTO student_preferences (id, user_id, target_roles, preferred_domains, open_to_remote, career_transition, timeline_months, experience_level) "
                "VALUES (:id, :user_id, '[\"Software Engineer\"]', '[\"Web\"]', 1, 0, 12, 'entry')"
            ),
            {"id": uuid.uuid4().hex, "user_id": sample_user.id.hex}
        )
    else:
        preference = StudentPreference(
            user_id=sample_user.id,
            target_roles=["Software Engineer"],
            preferred_domains=["Web"],
            open_to_remote=True,
            career_transition=False,
            experience_level="entry"
        )
        db_session.add(preference)
    db_session.commit()

    # Seed 2 taxonomy skills
    t1 = SkillTaxonomy(skill_name="Python", category="backend", skill_type="tool")
    t2 = SkillTaxonomy(skill_name="JS", category="frontend", skill_type="tool")
    db_session.add_all([t1, t2])
    db_session.commit()
    db_session.refresh(t1)
    db_session.refresh(t2)

    # Seed job requirements for "Software Engineer" with different review dates
    date_oldest = datetime.utcnow() - timedelta(days=30)
    date_newest = datetime.utcnow() - timedelta(days=10)

    db_session.execute(
        text(
            "INSERT INTO job_skill_requirements (id, job_role, skill_id, importance, min_score_required, last_reviewed_at) "
            "VALUES "
            f"('{uuid_str()}', 'Software Engineer', '{t1.id}', 'must_have', 70.0, :oldest), "
            f"('{uuid_str()}', 'Software Engineer', '{t2.id}', 'preferred', 70.0, :newest)"
        ),
        {"oldest": date_oldest, "newest": date_newest}
    )
    db_session.commit()

    # Trigger gap engine computation to populate SkillGap table
    from app.modules.skills.engine import compute_gaps_for_student
    compute_gaps_for_student(db_session, str(sample_user.id))

    # Get recommendations
    resp = auth_client.get("/api/skills/recommendations")
    assert resp.status_code == 200
    data = resp.json()

    # Validate recommendations structure and date
    primary = data["recommendations"]["primary"]
    assert primary["job_role"] == "Software Engineer"
    assert primary["requirements_last_reviewed"] is not None
    parsed_date = datetime.fromisoformat(primary["requirements_last_reviewed"].replace("Z", "+00:00"))
    assert (parsed_date - date_oldest.replace(tzinfo=parsed_date.tzinfo)).total_seconds() == pytest.approx(0, abs=2)


