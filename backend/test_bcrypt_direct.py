#!/usr/bin/env python3
"""Test bcrypt directly without passlib"""
import bcrypt

stored_hash = b"$2b$12$5Z74qkmhs0wK1S1MyQBWjOZlYMXRx9wdP4ZQ81y5/3ZnO0FP2LkqO"
password = b"STU001@123"

print(f"Password: {password}")
print(f"Hash: {stored_hash}")

try:
    result = bcrypt.checkpw(password, stored_hash)
    print(f"SUCCESS! Result: {result}")
except Exception as e:
    print(f"ERROR: {e}")
