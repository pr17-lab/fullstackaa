#!/usr/bin/env python3
"""Test password verification with the exact hash from database"""
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Exact hash from database
stored_hash = "$2b$12$5Z74qkmhs0wK1S1MyQBWjOZlYMXRx9wdP4ZQ81y5/3ZnO0FP2LkqO"
test_password = "STU001@123"

print(f"Stored hash: {stored_hash}")
print(f"Hash length: {len(stored_hash)}")
print(f"Test password: {test_password}")
print(f"Password length: {len(test_password)}")

try:
    print("\nAttempting verification...")
    result = pwd_context.verify(test_password, stored_hash)
    print(f"SUCCESS! Verification result: {result}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
