from app.core.database import SessionLocal
from app.models import AcademicTerm, StudentProfile, Subject

db = SessionLocal()

# Check GPA scale
terms = db.query(AcademicTerm).limit(20).all()
gpas = [float(t.gpa) for t in terms]

print("Sample GPAs from database:")
for gpa in gpas[:10]:
    print(f"  {gpa:.2f}")

max_gpa = max(float(t.gpa) for t in db.query(AcademicTerm).all())
min_gpa = min(float(t.gpa) for t in db.query(AcademicTerm).all())

print(f"\nGPA Range: {min_gpa:.2f} to {max_gpa:.2f}")
print(f"Scale detected: {'4.0 point scale' if max_gpa <= 4.5 else '10 point scale'}")

# Check Sanjay Kumar's data
student = db.query(StudentProfile).filter(StudentProfile.name == "Sanjay Kumar").first()
if student:
    term = db.query(AcademicTerm).filter(AcademicTerm.user_id == student.user_id).first()
    if term:
        subjects = db.query(Subject).filter(Subject.term_id == term.id).all()
        avg_marks = sum(float(s.marks) for s in subjects) / len(subjects) if subjects else 0
        
        print(f"\nSanjay Kumar:")
        print(f"  Stored GPA: {float(term.gpa):.2f}")
        print(f"  Average Marks: {avg_marks:.2f}")
        print(f"  Expected GPA (marks/10): {avg_marks/10:.2f}")

db.close()
