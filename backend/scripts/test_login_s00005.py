"""Test login API for S00005"""
import requests

print("Testing S00005 login...")

# Using form data like the frontend does
data = {
    'username': 'S00005',
    'password': 'S00005@123'
}

response = requests.post(
    'http://localhost:8000/api/auth/login',
    data=data  # Form data, not JSON
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

if response.status_code == 200:
    print("\n✓ Login successful!")
    token = response.json()['access_token']
    print(f"Token: {token[:50]}...")
    
    # Test /auth/me
    print("\nTesting /auth/me...")
    me_response = requests.get(
        'http://localhost:8000/api/auth/me',
        headers={'Authorization': f'Bearer {token}'}
    )
    print(f"Status: {me_response.status_code}")
    print(f"User: {me_response.json()}")
else:
    print("\n✗ Login failed!")
