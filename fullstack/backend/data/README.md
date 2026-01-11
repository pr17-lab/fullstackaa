# CSV Data Files

This directory contains CSV datasets used by the Student Academic Tracker application.

## Files

### SATA_student_main_info_10k.csv
Student profile information including:
- student_id: Unique identifier
- name: Full name
- email: Email address
- department: Academic department
- year_of_passout: Expected graduation year
- current_semester: Current semester number
- cgpa: Cumulative GPA
- status: Student status (Active/Inactive)

### SATA_academic_records_10k.csv
Academic performance records including:
- student_id: Student identifier (foreign key)
- semester: Semester number
- subject_code: Subject code
- subject_name: Subject name
- credits: Course credits
- Total_marks: Marks obtained
- pass_fail: Pass/Fail status
- performance_comment: Faculty comments

## Usage

These files are loaded into memory at application startup via the CSV data loader service. 
Access the data through API endpoints:
- /api/students/{student_id}
- /api/students/{student_id}/records
- /api/analytics/gpa-trend/{student_id}

## Security

**IMPORTANT:** These CSV files should NOT be:
- Exposed via frontend static file serving
- Committed to public repositories (if containing real data)
- Accessible directly via HTTP requests

The files are accessed only through controlled backend API endpoints with proper validation.
