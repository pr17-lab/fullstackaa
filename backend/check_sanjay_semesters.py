from app.core.database import SessionLocal
from app.models import StudentProfile, AcademicTerm
from sqlalchemy import func

db = SessionLocal()

# Find Sanjay Kumar
student = db.query(StudentProfile).filter(StudentProfile.name == "Sanjay Kumar").first()

if student:
    print(f"Student: {student.name}")
    print(f"Student ID: {student.student_id if hasattr(student, 'student_id') else 'N/A'}")
    
    # Get all academic terms
    terms = db.query(AcademicTerm).filter(
        AcademicTerm.user_id == student.user_id
    ).order_by(AcademicTerm.year, AcademicTerm.semester).all()
    
    print(f"\nTotal academic terms found: {len(terms)}")
    print("\nSemester breakdown:")
    for term in terms:
        print(f"  Semester {term.semester} ({term.year}): GPA = {float(term.gpa):.2f}")
    
    # Check which semesters are missing
    existing_semesters = set(t.semester for t in terms)
    expected_semesters = set(range(1, 9))  # Semesters 1-8
    missing_semesters = expected_semesters - existing_semesters
    
    if missing_semesters:
        print(f"\nMissing semesters: {sorted(missing_semesters)}")
    else:
        print("\nAll semesters (1-8) have records")

db.close()
