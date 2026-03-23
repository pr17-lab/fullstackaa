import requests

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzYW5qYXkua3VtYXIwMDFAY29sbGVnZS5lZHUiLCJ1c2VyX2lkIjoiMTA1NDdkM2YtYWQ5NS00NjI2LWEzNGMtZWFiZGU4N2Q1YTlhIiwic3R1ZGVudF9pZCI6IlMwMDAwMSIsImV4cCI6MTc3NDIxNTM1OX0.tsm9Z-MMWhxG0P9n9fXBy2HTUcZXBcTFf7mkAVGtNks"

print("\n=== STEP 3: fetchCurrentUser (/api/auth/me) ===")
try:
    r = requests.get(
        "http://localhost:8000/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    print("Status:", r.status_code)
    print("Headers:", dict(r.headers))
    print("Body:", r.text)
except Exception as e:
    print("Error:", e)
