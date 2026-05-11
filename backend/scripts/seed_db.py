import asyncio
import uuid
import random
from faker import Faker
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.student_profile import StudentProfile
from app.models.academic_term import AcademicTerm
from app.models.subject import Subject
from app.core.security import get_password_hash

fake = Faker()

async def seed_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with SessionLocal() as db:
        print("Starting database seed...")
        
        departments = ["CSE", "ECE", "MECH", "CIVIL", "EE"]
        
        for i in range(50):
            # Create user
            student_id = f"S2024{random.randint(100, 999)}{i:02d}"
            user = User(
                student_id=student_id,
                email=fake.unique.email(),
                password_hash=get_password_hash("password123"),
                role=UserRole.student,
                is_active=True
            )
            db.add(user)
            await db.flush() # flush to get user.id
            
            # Create profile
            semester = random.randint(1, 8)
            cgpa = round(random.uniform(5.0, 10.0), 2)
            profile = StudentProfile(
                user_id=user.id,
                name=fake.name(),
                department=random.choice(departments),
                batch_year=2024 - (semester // 2),
                semester=semester,
                performance_status="Good" if cgpa >= 7.5 else "Average",
                cgpa=cgpa,
                cgpa_10scale=cgpa,
                backlog_count=0,
                active_backlog=False
            )
            db.add(profile)
            await db.flush()
            
            # Create academic terms up to their semester
            for sem in range(1, semester + 1):
                term = AcademicTerm(
                    user_id=user.id,
                    semester=sem,
                    year=profile.batch_year + ((sem - 1) // 2),
                    gpa=round(random.uniform(max(4.0, cgpa - 1), min(10.0, cgpa + 1)), 2)
                )
                db.add(term)
                await db.flush()
                
                # Create subjects for term
                for subj_idx in range(1, 6): # 5 subjects per term
                    marks = int(random.uniform(40, 100))
                    subject = Subject(
                        term_id=term.id,
                        subject_name=f"{profile.department} Subject {sem}{subj_idx}",
                        subject_code=f"{profile.department}{sem}{subj_idx}",
                        credits=random.choice([3, 4]),
                        marks=marks,
                        total_marks=100,
                        pass_fail="Pass" if marks >= 40 else "F"
                    )
                    db.add(subject)
        
        await db.commit()
        print("Successfully seeded 50 students.")

if __name__ == "__main__":
    asyncio.run(seed_database())
