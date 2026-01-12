# Student Academic Tracker - Backend

## Overview
FastAPI backend for the Student Academic Tracker application.

## Setup

1. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
copy .env.example .env
# Edit .env with your configuration
```

4. Initialize database:
```bash
alembic upgrade head
```

5. Run development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation
Access Swagger UI at: http://localhost:8000/docs

### CSV Data Endpoints
The application includes pre-loaded CSV datasets for demonstration:
- **GET /api/students/{student_id}** - Get student information by ID
- **GET /api/students/{student_id}/records** - Get academic records for a student
- **GET /api/analytics/gpa-trend/{student_id}** - Get GPA trend by semester
- **GET /api/students** - Search students with filters (department, semester, min_cgpa)
- **GET /api/health/csv-data** - Check CSV data loading status

### Data Sources
The backend includes two CSV datasets:
- `SATA_student_main_info_10k.csv` - Student profile information
- `SATA_academic_records_10k.csv` - Academic performance records

**Schema:**

Student Info:
- student_id, name, email, department, year_of_passout, current_semester, cgpa, status

Academic Records:
- student_id, semester, subject_code, subject_name, credits, Total_marks, pass_fail, performance_comment

**Security Note:** CSV files are stored in `backend/data/` and are NOT exposed publicly via the frontend. They are loaded into memory at server startup and accessed only through controlled API endpoints.

## Project Structure
- `app/` - Application code
  - `core/` - Configuration, security, database
  - `models/` - SQLAlchemy ORM models
  - `schemas/` - Pydantic request/response schemas
  - `api/` - API routes and dependencies
  - `services/` - Business logic layer (includes CSV data loader)
  - `utils/` - Utility functions
- `data/` - CSV data files (not exposed publicly)
- `alembic/` - Database migrations
- `tests/` - Test suite

