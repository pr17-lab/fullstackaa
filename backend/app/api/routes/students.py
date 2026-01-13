from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
import uuid

from app.core.database import get_db
from app.models import StudentProfile, User, AcademicTerm, Subject
from app.schemas import (
    StudentProfileCreate,
    StudentProfileUpdate,
    StudentProfileResponse,
    StudentListResponse,
    AcademicRecordSummary,
    AcademicTermResponse
)

router = APIRouter()

@router.get("/students", response_model=StudentListResponse)
async def list_students(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    branch: Optional[str] = Query(None, description="Filter by branch"),
    semester: Optional[int] = Query(None, ge=1, le=10, description="Filter by semester"),
    db: Session = Depends(get_db)
):
    """Get paginated list of all students with optional filters."""
    query = db.query(StudentProfile)
    
    # Apply filters
    if branch:
        query = query.filter(StudentProfile.branch == branch)
    if semester:
        query = query.filter(StudentProfile.semester == semester)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    students = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return StudentListResponse(
        total=total,
        page=page,
        page_size=page_size,
        students=students
    )

@router.get("/students/{student_id}", response_model=StudentProfileResponse)
async def get_student(
    student_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get student profile by ID."""
    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    
    if not student:
        raise HTTPException(
            status_code=404,
            detail=f"Student with ID {student_id} not found"
        )
    
    return student

@router.post("/students", response_model=StudentProfileResponse, status_code=201)
async def create_student(
    student_data: StudentProfileCreate,
    db: Session = Depends(get_db)
):
    """Create a new student profile."""
    # Check if user exists
    user = db.query(User).filter(User.id == student_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User with ID {student_data.user_id} not found"
        )
    
    # Check if student profile already exists for this user
    existing = db.query(StudentProfile).filter(
        StudentProfile.user_id == student_data.user_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Student profile already exists for user {student_data.user_id}"
        )
    
    # Create new student profile
    student = StudentProfile(**student_data.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    
    return student

@router.put("/students/{student_id}", response_model=StudentProfileResponse)
async def update_student(
    student_id: uuid.UUID,
    student_data: StudentProfileUpdate,
    db: Session = Depends(get_db)
):
    """Update student profile."""
    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    
    if not student:
        raise HTTPException(
            status_code=404,
            detail=f"Student with ID {student_id} not found"
        )
    
    # Update only provided fields
    update_data = student_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(student, field, value)
    
    db.commit()
    db.refresh(student)
    
    return student

@router.delete("/students/{student_id}", status_code=204)
async def delete_student(
    student_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Delete student profile."""
    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    
    if not student:
        raise HTTPException(
            status_code=404,
            detail=f"Student with ID {student_id} not found"
        )
    
    db.delete(student)
    db.commit()
    
    return None

@router.get("/students/{student_id}/academic-records", response_model=AcademicRecordSummary)
async def get_student_academic_records(
    student_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get complete academic history for a student."""
    try:
        # Verify student exists
        student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
        
        if not student:
            raise HTTPException(
                status_code=404,
                detail=f"Student with ID {student_id} not found"
            )
        
        # Get all academic terms with subjects (eager loading)
        terms = db.query(AcademicTerm).options(
            joinedload(AcademicTerm.subjects)
        ).filter(
            AcademicTerm.user_id == student.user_id
        ).order_by(AcademicTerm.year, AcademicTerm.semester).all()
        
        # Calculate overall statistics with defensive handling
        if terms and len(terms) > 0:
            # Safe GPA calculation
            overall_gpa = sum(float(term.gpa) for term in terms) / len(terms)
            
            # Safe credits calculation
            total_credits = 0
            for term in terms:
                if term.subjects:
                    # Ensure credits exist and are valid before summing
                    total_credits += sum(
                        subject.credits for subject in term.subjects 
                        if subject.credits is not None
                    )
        else:
            # Return empty academic record for students with no data
            overall_gpa = 0.0
            total_credits = 0
        
        return AcademicRecordSummary(
            student_id=student_id,
            total_terms=len(terms),
            overall_gpa=overall_gpa,
            total_credits=total_credits,
            terms=terms
        )
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        # Log and return the actual error for debugging
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching academic records: {str(e)}"
        )


