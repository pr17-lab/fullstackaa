import traceback, sys

try:
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    res = client.post('/api/auth/login', data={'username': 'S00001', 'password': 'S00001@123'})
    print('Login status:', res.status_code)
    print(res.text[:500])
except Exception as e:
    tb = traceback.format_exc()
    with open('err.txt', 'w', encoding='utf-8') as f:
        f.write(tb)
    print(tb)
