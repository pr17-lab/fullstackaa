"""
Test authentication with multiple student IDs
"""
import requests
import json

# Test multiple students
students = [
    ('S01968', 'S01968@123'),
    ('S01977', 'S01977@123'),
    ('S00001', 'S00001@123'),
    ('S00100', 'S00100@123'),
    ('S05000', 'S05000@123'),
]

print('='*60)
print('TESTING AUTHENTICATION WITH MULTIPLE STUDENTS')
print('='*60)

success_count = 0
fail_count = 0

for student_id, password in students:
    try:
        # Use form data for OAuth2PasswordRequestForm
        response = requests.post(
            'http://localhost:8000/api/auth/login',
            data={'username': student_id, 'password': password},  # Changed to form data
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f'\nStudent {student_id}: SUCCESS')
            print(f'  Token: {data.get("access_token", "")[:30]}...')
            success_count += 1
        else:
            print(f'\nStudent {student_id}: FAILED')
            print(f'  Status: {response.status_code}')
            print(f'  Error: {response.text[:100]}')
            fail_count += 1
    except Exception as e:
        print(f'\nStudent {student_id}: ERROR')
        print(f'  {str(e)[:100]}')
        fail_count += 1

print('\n' + '='*60)
print(f'SUMMARY: {success_count} SUCCESS, {fail_count} FAILED')
print('='*60)
