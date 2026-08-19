import uuid
import pytest
import sqlite3
import json
sqlite3.register_adapter(list, json.dumps)

from app.models.student_preference import StudentPreference
from app.models.skill_taxonomy import SkillTaxonomy
from app.models.job_skill_requirement import JobSkillRequirement
from app.models.roadmap import Roadmap, RoadmapTask
from app.models.skill_gap import SkillGap
from app.modules.preferences.service import derive_preferred_domains
from app.modules.roadmap.service import generate_roadmap

def test_derive_preferred_domains():
    # Single domain Software
    assert derive_preferred_domains(["Software Engineer", "Backend Developer"]) == ["Software"]
    # Single domain Data
    assert derive_preferred_domains(["Data Analyst", "Data Engineer"]) == ["Data"]
    # Single domain AI/ML
    assert derive_preferred_domains(["AI Engineer", "Computer Vision Engineer"]) == ["AI/ML"]
    # Multiple domains
    assert derive_preferred_domains(["Software Engineer", "Data Scientist", "AI Engineer"]) == ["AI/ML", "Data", "Software"]
    # Unknown role
    assert derive_preferred_domains(["Unknown Role"]) == []
    # Empty
    assert derive_preferred_domains([]) == []

def test_create_preferences_omitted_defaults(auth_client, db_session, sample_user, sample_student_profile):
    # Clear any existing student_preferences for sample_user
    db_session.query(StudentPreference).filter(StudentPreference.user_id == sample_user.id).delete()
    db_session.commit()

    payload = {
        "target_roles": ["Software Engineer", "Data Scientist"],
        "open_to_remote": True,
        "career_transition": False,
        "timeline_months": 6,
        "available_hours_per_week": 10
    }
    response = auth_client.post("/api/preferences", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # Verify they were saved to DB
    db_pref = db_session.query(StudentPreference).filter(StudentPreference.user_id == sample_user.id).first()
    assert db_pref is not None
    
    # Assert defaulted/derived values in response
    assert data["experience_level"] == "fresher"
    assert sorted(data["preferred_domains"]) == ["Data", "Software"]

    assert db_pref.experience_level == "fresher"
    assert sorted(db_pref.preferred_domains) == ["Data", "Software"]

def test_update_preferences_does_not_overwrite(auth_client, db_session, sample_user, sample_student_profile):
    # Setup existing preference in DB with specific values
    db_session.query(StudentPreference).filter(StudentPreference.user_id == sample_user.id).delete()
    db_session.commit()

    pref = StudentPreference(
        id=uuid.uuid4(),
        user_id=sample_user.id,
        target_roles=["Backend Developer"],
        preferred_domains=["Custom Domain"],
        experience_level="junior",
        timeline_months=6,
        open_to_remote=True
    )
    db_session.add(pref)
    db_session.commit()

    # Update preferences omitting those fields
    payload = {
        "target_roles": ["Backend Developer", "Frontend Developer"],
        "open_to_remote": True,
        "career_transition": False,
        "timeline_months": 12,
        "available_hours_per_week": 20
    }
    response = auth_client.put("/api/preferences", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Verify they were NOT overwritten
    assert data["experience_level"] == "junior"
    assert data["preferred_domains"] == ["Custom Domain"]

def test_new_roles_gap_analysis_and_roadmap_generation(auth_client, db_session, sample_user, sample_student_profile):
    import csv
    import os
    from app.models.learning_resource import LearningResource

    # Compute base path for data folder relative to this file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    taxonomy_path = os.path.join(base_dir, 'data', 'skill_taxonomy.csv')
    requirements_path = os.path.join(base_dir, 'data', 'job_skill_requirements.csv')

    # Delete existing requirements/skills to ensure clean state
    db_session.query(JobSkillRequirement).delete()
    db_session.query(SkillTaxonomy).delete()
    db_session.commit()

    # Seed skill taxonomy and learning resources from CSV
    skills = {}
    with open(taxonomy_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sk = SkillTaxonomy(
                id=uuid.UUID(row['id']),
                skill_name=row['skill_name'],
                category=row['category'],
                aliases=row['aliases'].split('|') if row['aliases'] else [],
                description=row['description'],
                skill_type='concept'
            )
            db_session.add(sk)
            db_session.flush()
            skills[row['skill_name'].lower()] = sk
            
            # Seed Course/Learn Resource
            db_session.add(LearningResource(
                id=uuid.uuid4(),
                skill_id=sk.id,
                title=f"Learn {row['skill_name']} Course",
                resource_url="https://example.com/learn",
                platform="Coursera",
                phase="learn",
                upvotes=10,
                downvotes=0
            ))
            # Seed Practice Resource
            db_session.add(LearningResource(
                id=uuid.uuid4(),
                skill_id=sk.id,
                title=f"Practice {row['skill_name']} Exercises",
                resource_url="https://example.com/practice",
                platform="LeetCode",
                phase="practice",
                upvotes=10,
                downvotes=0
            ))
    db_session.commit()

    # Seed new role requirements from CSV
    with open(requirements_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            req = JobSkillRequirement(
                id=uuid.UUID(row['id']),
                job_role=row['job_role'],
                skill_id=uuid.UUID(row['skill_id']),
                importance=row['importance'],
                min_score_required=float(row['min_score_required'])
            )
            db_session.add(req)
    db_session.commit()

    # Assertions on Taxonomy and Requirements depth/weighting
    # 1. Check count of requirements for each role is in 10-15 range
    for role in ["AI Engineer", "Computer Vision Engineer", "MLOps Engineer"]:
        reqs = db_session.query(JobSkillRequirement).filter(JobSkillRequirement.job_role == role).all()
        assert 10 <= len(reqs) <= 15, f"{role} has {len(reqs)} skills, which is not in the 10-15 range"

    # 2. Check MLOps Engineer's weighting meaningfully de-emphasizes Machine Learning
    ml_id = uuid.UUID("8fc9258e-c3eb-4542-9a05-d9ecabc0188b")
    mlops_ml_req = db_session.query(JobSkillRequirement).filter(
        JobSkillRequirement.job_role == "MLOps Engineer",
        JobSkillRequirement.skill_id == ml_id
    ).first()
    assert mlops_ml_req is not None
    assert mlops_ml_req.importance == "preferred"
    assert mlops_ml_req.min_score_required == 55.0

    # Ensure other roles still have Machine Learning as must_have
    for role in ["AI Engineer", "Computer Vision Engineer"]:
        other_ml_req = db_session.query(JobSkillRequirement).filter(
            JobSkillRequirement.job_role == role,
            JobSkillRequirement.skill_id == ml_id
        ).first()
        assert other_ml_req is not None
        assert other_ml_req.importance == "must_have"
        assert other_ml_req.min_score_required == 70.0

    # 3. Check no duplicate skill_taxonomy entries exist
    all_skills = db_session.query(SkillTaxonomy).all()
    names = [s.skill_name.lower() for s in all_skills]
    assert len(names) == len(set(names)), "Duplicate skill names exist in taxonomy"

    # Test for each of the new roles
    for role in ["AI Engineer", "Computer Vision Engineer", "MLOps Engineer"]:
        # 1. Update preferences to target this role
        db_session.query(StudentPreference).filter(StudentPreference.user_id == sample_user.id).delete()
        pref = StudentPreference(
            id=uuid.uuid4(),
            user_id=sample_user.id,
            target_roles=[role],
            preferred_domains=["AI/ML"],
            experience_level="fresher",
            timeline_months=6,
            open_to_remote=True
        )
        db_session.add(pref)
        db_session.commit()

        # 1.5 Compute gaps programmatically to update SkillGap table
        from app.modules.skills.engine import compute_gaps_for_student
        compute_gaps_for_student(db_session, str(sample_user.id))

        # 2. Call career recommendations (gap analysis)
        response_career = auth_client.get("/api/skills/recommendations")
        assert response_career.status_code == 200
        career_data = response_career.json()
        
        # Verify our role is listed in career recommendation tiers
        found_role = False
        for tier in ["excellent", "good", "potential", "low"]:
            if tier in career_data["tiers"]:
                for rec in career_data["tiers"][tier]:
                    if rec["job_role"] == role:
                        found_role = True
                        # Verify it has distinct requirements
                        assert rec["match_score"] is not None
                        assert "missing_skills" in rec
        assert found_role, f"Role {role} was not analyzed in career recommendations"

        # 3. Test roadmap generation
        db_session.query(Roadmap).filter(Roadmap.user_id == sample_user.id).delete()
        db_session.commit()

        # Call generate_roadmap service function
        import asyncio
        roadmap = asyncio.run(generate_roadmap(db_session, sample_user.id, role))
        assert roadmap is not None
        assert roadmap.job_role == role
        
        # Check that tasks were generated for the role's specific skills
        tasks = db_session.query(RoadmapTask).filter(RoadmapTask.roadmap_id == roadmap.id).all()
        assert len(tasks) > 0
        
        # Verify tasks are distinct and match the role's skills
        task_skills = [db_session.query(SkillTaxonomy).get(t.associated_skill_id).skill_name for t in tasks]
        reqs = db_session.query(JobSkillRequirement).filter(JobSkillRequirement.job_role == role).all()
        expected_skills = [db_session.query(SkillTaxonomy).get(r.skill_id).skill_name for r in reqs]
        for t_skill in task_skills:
            assert t_skill in expected_skills
