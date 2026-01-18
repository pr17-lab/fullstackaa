import sys
sys.path.insert(0, '.')
from app.models import User, StudentProfile, AcademicTerm, Subject
from app.core.database import SessionLocal

session = SessionLocal()

print("=" * 80)
print("DATABASE SUMMARY")
print("=" * 80)

user_count = session.query(User).count()
profile_count = session.query(StudentProfile).count()
term_count = session.query(AcademicTerm).count()
subject_count = session.query(Subject).count()

print(f"\nUsers: {user_count:,}")
print(f"Student Profiles: {profile_count:,}")
print(f"Academic Terms: {term_count:,}")
print(f"Subjects: {subject_count:,}")

print(f"\nAverages:")
if user_count > 0:
    print(f"  - Terms per student: {term_count / user_count:.1f}")
    print(f"  - Subjects per student: {subject_count / user_count:.1f}")
    if term_count > 0:
        print(f"  - Subjects per term: {subject_count / term_count:.1f}")

# Sample data
print(f"\nSample student with academic records:")
sample_user = session.query(User).filter(User.student_id == 'S00001').first()
if sample_user:
    terms = session.query(AcademicTerm).filter(AcademicTerm.user_id == sample_user.id).all()
    print(f"  Student: {sample_user.student_id}")
    print(f"  Terms: {len(terms)}")
    if terms:
        first_term = terms[0]
        subjects = session.query(Subject).filter(Subject.term_id == first_term.id).all()
        print(f"  Sample term: Semester {first_term.semester}, GPA {first_term.gpa}")
        print(f"  Subjects in term: {len(subjects)}")

session.close()
