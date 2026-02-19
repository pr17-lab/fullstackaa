from app.core.database import SessionLocal
from app.models import User, StudentProfile, AcademicTerm, Subject
from sqlalchemy import func

db = SessionLocal()

# Find Sanjay Kumar
student = db.query(StudentProfile).filter(StudentProfile.name == 'Sanjay Kumar').first()

if student:
    print(f"Student: {student.name}, Current Semester: {student.semester}")
    print(f"User ID: {student.user_id}")
    
    # Get academic terms
    terms = db.query(AcademicTerm).filter(
        AcademicTerm.user_id == student.user_id
    ).order_by(AcademicTerm.semester).all()
    
    print(f"\nTotal terms in database: {len(terms)}")
    for term in terms:
        print(f"  Semester {term.semester} ({term.year}): GPA={term.gpa}")
        
        # Get subjects for this term
        subjects = db.query(Subject).filter(Subject.term_id == term.id).all()
        print(f"    Subjects: {len(subjects)}")
        for subj in subjects:
            print(f"      - {subj.subject_name}: {subj.marks}")
    
    # Check for Database Systems specifically
    print("\n--- Checking Database Systems subjects ---")
    all_subjects = db.query(Subject).join(AcademicTerm).filter(
        AcademicTerm.user_id == student.user_id
    ).all()
    
    db_systems_subjects = [s for s in all_subjects if 'Database' in s.subject_name]
    print(f"\nFound {len(db_systems_subjects)} Database-related subjects:")
    for subj in db_systems_subjects:
        term = db.query(AcademicTerm).filter(AcademicTerm.id == subj.term_id).first()
        print(f"  - {subj.subject_name} (Sem {term.semester}): {subj.marks} marks")
    
    # Get all subjects sorted by marks
    print("\n--- All subjects sorted by marks ---")
    all_subj_sorted = sorted(all_subjects, key=lambda x: x.marks)
    print("Weakest 3:")
    for i, subj in enumerate(all_subj_sorted[:3]):
        term = db.query(AcademicTerm).filter(AcademicTerm.id == subj.term_id).first()
        print(f"  {i+1}. {subj.subject_name} (Sem {term.semester}): {subj.marks}")
    
    print("\nStrongest 3:")
    for i, subj in enumerate(all_subj_sorted[-3:][::-1]):
        term = db.query(AcademicTerm).filter(AcademicTerm.id == subj.term_id).first()
        print(f"  {i+1}. {subj.subject_name} (Sem {term.semester}): {subj.marks}")
else:
    print("Student 'Sanjay Kumar' not found")

db.close()
