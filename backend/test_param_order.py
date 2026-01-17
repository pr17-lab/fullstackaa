#!/usr/bin/env python3
"""Test parameter order for verify function - write to file"""
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

stored_hash = "$2b$12$5Z74qkmhs0wK1S1MyQBWjOZlYMXRx9wdP4ZQ81y5/3ZnO0FP2LkqO"
test_password = "STU001@123"

with open("verify_test_results.txt", "w") as f:
    f.write("=== TEST 1: password first, hash second (CORRECT) ===\n")
    try:
        result = pwd_context.verify(test_password, stored_hash)
        f.write(f"SUCCESS! Result: {result}\n")
    except Exception as e:
        f.write(f"ERROR: {e}\n")
    
    f.write("\n=== TEST 2: hash first, password second (WRONG) ===\n")
    try:
        result = pwd_context.verify(stored_hash, test_password)
        f.write(f"SUCCESS! Result: {result}\n")
    except Exception as e:
        f.write(f"ERROR: {e}\n")

print("Results written to verify_test_results.txt")
