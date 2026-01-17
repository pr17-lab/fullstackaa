#!/usr/bin/env python3
"""
Quick test to show password hash WITHOUT attempting verification
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from app.core.config import settings

# Create database connection
engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text(
        "SELECT email, password_hash, LENGTH(password_hash) as hash_len FROM users WHERE email = 'priya.sharma@example.com'"
    ))
    
    for row in result:
        print(f"Email: {row.email}")
        print(f"Hash length: {row.hash_len}")
        print(f"Hash value (raw): {row.password_hash}")
        print(f"\nHash type: {type(row.password_hash)}")
        print(f"Hash repr: {repr(row.password_hash)}")
