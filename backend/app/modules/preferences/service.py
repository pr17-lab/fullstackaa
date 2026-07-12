from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from app.models.student_preference import StudentPreference
from .schemas import PreferenceCreate, PreferenceUpdate

def get_preferences(db: Session, user_id: UUID) -> StudentPreference:
    return db.query(StudentPreference).filter(StudentPreference.user_id == user_id).first()

def derive_preferred_domains(target_roles: list[str]) -> list[str]:
    mapping = {
        "Software Engineer": "Software",
        "Frontend Developer": "Software",
        "Backend Developer": "Software",
        "Full Stack Developer": "Software",
        "DevOps Engineer": "Software",
        "Cybersecurity Analyst": "Software",
        
        "Data Scientist": "Data",
        "Data Engineer": "Data",
        "Data Analyst": "Data",
        
        "Machine Learning Engineer": "AI/ML",
        "AI Engineer": "AI/ML",
        "NLP Engineer": "AI/ML",
        "Computer Vision Engineer": "AI/ML",
        "MLOps Engineer": "AI/ML",
    }
    domains = set()
    for role in target_roles:
        domain = mapping.get(role)
        if domain:
            domains.add(domain)
    return sorted(list(domains))

def create_preferences(db: Session, user_id: UUID, data: PreferenceCreate) -> StudentPreference:
    db_pref = get_preferences(db, user_id)
    if db_pref:
        return db_pref
    
    exp_level = data.experience_level if data.experience_level is not None else "fresher"
    pref_domains = data.preferred_domains if data.preferred_domains is not None else derive_preferred_domains(data.target_roles)

    db_pref = StudentPreference(
        user_id=user_id,
        target_roles=data.target_roles,
        preferred_domains=pref_domains,
        open_to_remote=data.open_to_remote,
        career_transition=data.career_transition,
        transition_from=data.transition_from,
        transition_to=data.transition_to,
        timeline_months=data.timeline_months,
        experience_level=exp_level,
        available_hours_per_week=data.available_hours_per_week,
        onboarding_step=data.onboarding_step
    )
    db.add(db_pref)
    db.commit()
    db.refresh(db_pref)
    return db_pref

def update_preferences(db: Session, user_id: UUID, data: PreferenceUpdate) -> StudentPreference:
    db_pref = get_preferences(db, user_id)
    if not db_pref:
        # Upsert behavior
        return create_preferences(db, user_id, PreferenceCreate(**data.model_dump()))
        
    for key, value in data.model_dump().items():
        if key == 'experience_level' and value is None:
            if getattr(db_pref, key) is None:
                setattr(db_pref, key, "fresher")
        elif key == 'preferred_domains' and value is None:
            if getattr(db_pref, key) is None:
                setattr(db_pref, key, derive_preferred_domains(data.target_roles))
        else:
            setattr(db_pref, key, value)
    
    db.commit()
    db.refresh(db_pref)
    return db_pref
