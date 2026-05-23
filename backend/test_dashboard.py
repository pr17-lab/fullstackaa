import httpx
import sys

def main():
    client = httpx.Client(base_url="http://localhost:8000")
    
    # login
    # S10000,cnnGfw2N2xEM,divya.reddy000@student.edu
    res = client.post("/api/auth/login", data={
        "username": "S10000",
        "password": "cnnGfw2N2xEM"
    })
    
    if res.status_code != 200:
        print("Login failed:", res.text)
        sys.exit(1)
        
    token = res.json()["access_token"]
    print("Logged in!")
    
    client.headers.update({"Authorization": f"Bearer {token}"})
    
    # get me
    res_me = client.get("/api/auth/me")
    if res_me.status_code != 200:
        print("Me failed:", res_me.text)
        sys.exit(1)
        
    student_id = res_me.json()["id"]
    print(f"Student ID: {student_id}")
    
    # 1. academic-records
    res1 = client.get(f"/api/students/{student_id}/academic-records")
    print("academic-records:", res1.status_code, repr(res1.text[:100]))
    
    # 2. summary
    res2 = client.get(f"/api/analytics/student/{student_id}/summary")
    print("summary:", res2.status_code, repr(res2.text[:100]))
    
    # 3. recommendation
    res3 = client.get("/api/skills/recommendation")
    print("recommendation:", res3.status_code, repr(res3.text[:100]))

if __name__ == "__main__":
    main()
