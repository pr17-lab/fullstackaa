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
