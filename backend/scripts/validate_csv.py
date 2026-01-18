#!/usr/bin/env python3
"""
CSV Validation Script for Student Data Import

Validates CSV files before import to prevent data corruption.
Checks for duplicates, missing fields, invalid data, and format errors.

Usage:
    python backend/scripts/validate_csv.py data/SATA_student_main_info_10k_IEEE.csv
    python backend/scripts/validate_csv.py data/SATA_academic_records_10k_IEEE.csv
"""

import sys
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple


def validate_student_csv(csv_path: str) -> Tuple[bool, List[str]]:
    """
    Validate student CSV before import.
    
    Args:
        csv_path: Path to the student CSV file
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    warnings = []
    
    try:
        # Read CSV
        df = pd.read_csv(csv_path)
        total_rows = len(df)
        
        print(f"\n{'='*70}")
        print(f"VALIDATING STUDENT CSV: {Path(csv_path).name}")
        print(f"{'='*70}")
        print(f"Total rows: {total_rows}\n")
        
        # Check required columns
        required_cols = ['student_id', 'name', 'email', 'department', 'current_semester']
        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            errors.append(f"Missing required columns: {', '.join(missing_cols)}")
        
        # Check for duplicate emails
        dup_emails = df['email'].duplicated().sum()
        if dup_emails > 0:
            errors.append(f"Found {dup_emails} duplicate email addresses")
            # Show sample duplicates
            dup_rows = df[df['email'].duplicated(keep=False)].sort_values('email')
            print(f"⚠️  Sample duplicate emails:")
            for email in dup_rows['email'].unique()[:5]:
                count = (df['email'] == email).sum()
                print(f"   - {email} (appears {count} times)")
            print()
        
        # Check for duplicate student IDs
        dup_student_ids = df['student_id'].duplicated().sum()
        if dup_student_ids > 0:
            errors.append(f"Found {dup_student_ids} duplicate student IDs")
            # Show sample duplicates
            dup_rows = df[df['student_id'].duplicated(keep=False)].sort_values('student_id')
            print(f"⚠️  Sample duplicate student IDs:")
            for sid in dup_rows['student_id'].unique()[:5]:
                count = (df['student_id'] == sid).sum()
                print(f"   - {sid} (appears {count} times)")
            print()
        
        # Check for null values in required fields
        for col in required_cols:
            if col in df.columns:
                null_count = df[col].isnull().sum()
                if null_count > 0:
                    errors.append(f"{col}: {null_count} null/missing values ({null_count/total_rows*100:.1f}%)")
        
        # Validate data types
        if 'current_semester' in df.columns:
            try:
                pd.to_numeric(df['current_semester'], errors='coerce')
                invalid_semesters = df['current_semester'].isnull().sum()
                if invalid_semesters > 0:
                    warnings.append(f"current_semester: {invalid_semesters} non-numeric values")
            except Exception:
                errors.append("current_semester column has invalid data type")
        
        # Validate email format
        if 'email' in df.columns:
            invalid_emails = df[~df['email'].astype(str).str.contains('@', na=False)].shape[0]
            if invalid_emails > 0:
                errors.append(f"{invalid_emails} invalid email formats (missing '@')")
        
        # Check for empty strings
        for col in required_cols:
            if col in df.columns:
                empty_strings = (df[col].astype(str).str.strip() == '').sum()
                if empty_strings > 0:
                    warnings.append(f"{col}: {empty_strings} empty string values")
        
        # Print validation results
        print(f"VALIDATION RESULTS:")
        print(f"{'-'*70}")
        
        if not errors and not warnings:
            print("✅ All validation checks passed!")
        else:
            if errors:
                print(f"\n❌ ERRORS ({len(errors)}):")
                for i, error in enumerate(errors, 1):
                    print(f"   {i}. {error}")
            
            if warnings:
                print(f"\n⚠️  WARNINGS ({len(warnings)}):")
                for i, warning in enumerate(warnings, 1):
                    print(f"   {i}. {warning}")
        
        print(f"\n{'='*70}\n")
        
        return len(errors) == 0, errors
        
    except FileNotFoundError:
        errors.append(f"File not found: {csv_path}")
        return False, errors
    except pd.errors.EmptyDataError:
        errors.append("CSV file is empty")
        return False, errors
    except Exception as e:
        errors.append(f"Unexpected error: {str(e)}")
        return False, errors


def validate_academic_csv(csv_path: str) -> Tuple[bool, List[str]]:
    """
    Validate academic records CSV before import.
    
    Args:
        csv_path: Path to the academic records CSV file
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    warnings = []
    
    try:
        # Read CSV
        df = pd.read_csv(csv_path)
        total_rows = len(df)
        
        print(f"\n{'='*70}")
        print(f"VALIDATING ACADEMIC RECORDS CSV: {Path(csv_path).name}")
        print(f"{'='*70}")
        print(f"Total rows: {total_rows}\n")
        
        # Check required columns
        required_cols = ['student_id', 'semester', 'subject_code', 'subject_name', 
                        'credits', 'Total_marks']
        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            errors.append(f"Missing required columns: {', '.join(missing_cols)}")
        
        # Check for null values in required fields
        for col in required_cols:
            if col in df.columns:
                null_count = df[col].isnull().sum()
                if null_count > 0:
                    errors.append(f"{col}: {null_count} null/missing values ({null_count/total_rows*100:.1f}%)")
        
        # Validate numeric fields
        numeric_fields = ['semester', 'credits', 'Total_marks']
        for field in numeric_fields:
            if field in df.columns:
                try:
                    pd.to_numeric(df[field], errors='coerce')
                    invalid_count = df[field].isnull().sum()
                    if invalid_count > 0:
                        warnings.append(f"{field}: {invalid_count} non-numeric values")
                except Exception:
                    errors.append(f"{field} column has invalid data type")
        
        # Check for duplicate subject entries (same student, semester, subject_code)
        if all(col in df.columns for col in ['student_id', 'semester', 'subject_code']):
            duplicates = df.duplicated(subset=['student_id', 'semester', 'subject_code']).sum()
            if duplicates > 0:
                errors.append(f"Found {duplicates} duplicate subject entries (same student, semester, subject)")
        
        # Validate marks range (typically 0-100)
        if 'Total_marks' in df.columns:
            out_of_range = df[(df['Total_marks'] < 0) | (df['Total_marks'] > 100)].shape[0]
            if out_of_range > 0:
                warnings.append(f"Total_marks: {out_of_range} values outside normal range (0-100)")
        
        # Print validation results
        print(f"VALIDATION RESULTS:")
        print(f"{'-'*70}")
        
        if not errors and not warnings:
            print("✅ All validation checks passed!")
        else:
            if errors:
                print(f"\n❌ ERRORS ({len(errors)}):")
                for i, error in enumerate(errors, 1):
                    print(f"   {i}. {error}")
            
            if warnings:
                print(f"\n⚠️  WARNINGS ({len(warnings)}):")
                for i, warning in enumerate(warnings, 1):
                    print(f"   {i}. {warning}")
        
        print(f"\n{'='*70}\n")
        
        return len(errors) == 0, errors
        
    except FileNotFoundError:
        errors.append(f"File not found: {csv_path}")
        return False, errors
    except pd.errors.EmptyDataError:
        errors.append("CSV file is empty")
        return False, errors
    except Exception as e:
        errors.append(f"Unexpected error: {str(e)}")
        return False, errors


def main():
    """Main validation function."""
    if len(sys.argv) < 2:
        print("Usage: python validate_csv.py <csv_file_path>")
        print("\nExamples:")
        print("  python scripts/validate_csv.py data/SATA_student_main_info_10k_IEEE.csv")
        print("  python scripts/validate_csv.py data/SATA_academic_records_10k_IEEE.csv")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    
    # Determine CSV type based on filename
    filename = Path(csv_path).name.lower()
    
    if 'student_main_info' in filename or 'student_info' in filename:
        valid, errors = validate_student_csv(csv_path)
    elif 'academic_records' in filename or 'academic' in filename:
        valid, errors = validate_academic_csv(csv_path)
    else:
        print("⚠️  Warning: Could not determine CSV type from filename.")
        print("Attempting student CSV validation...\n")
        valid, errors = validate_student_csv(csv_path)
    
    if not valid:
        print("❌ VALIDATION FAILED - Import not recommended")
        sys.exit(1)
    else:
        print("✅ VALIDATION PASSED - Safe to import")
        sys.exit(0)


if __name__ == "__main__":
    main()
