import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def print_test(name, passed, details=""):
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name}")
    if details:
        print(f"       {details}")

def main():
    try:
        # 1. Login (OAuth2 Password Bearer uses form data)
        print("\n--- 1. Login ---")
        res = client.post("/api/auth/login", data={"username": "S00001", "password": "S00001@123"})
        if res.status_code == 200:
            token = res.json().get("access_token")
            print_test("POST /api/auth/login", True, "Successfully acquired JWT token")
        else:
            print_test("POST /api/auth/login", False, f"Status: {res.status_code} Body: {res.text}")
            return
            
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Get Summary
        print("\n--- 2. Skills Summary ---")
        res = client.get("/api/skills/summary", headers=headers)
        if res.status_code == 200:
            data = res.json()
            print_test("GET /api/skills/summary", True, f"Total Skills: {data.get('total_skills')}, Top Maps: {len(data.get('top_skills', []))}")
        else:
            print_test("GET /api/skills/summary", False, f"Status: {res.status_code} Body: {res.text}")

        # 3. Get Gaps
        print("\n--- 3. Skills Gaps ---")
        res = client.get("/api/skills/gaps", headers=headers)
        if res.status_code == 200:
            data = res.json()
            if len(data) > 0:
                print_test("GET /api/skills/gaps", True, f"Returned {len(data)} gaps. Top Gap: {data[0].get('job_role')} (Match: {data[0].get('match_score')}%) Label: {data[0].get('match_label')}")
            else:
                print_test("GET /api/skills/gaps", False, "No gaps returned")
        else:
            print_test("GET /api/skills/gaps", False, f"Status: {res.status_code} Body: {res.text}")
            
        # 4. Get Preferences
        print("\n--- 4. Preferences ---")
        res = client.get("/api/preferences", headers=headers)
        if res.status_code == 200:
            data = res.json()
            print_test("GET /api/preferences", True, f"Target Roles: {', '.join(data.get('target_roles', []))}")
        else:
            print_test("GET /api/preferences", False, f"Status: {res.status_code} Body: {res.text}")
            
        # 5. Generate Roadmap
        print("\n--- 5. Generate Roadmap ---")
        res = client.post("/api/roadmap/generate", headers=headers, json={"job_role": "Data Scientist"})
        if res.status_code == 200:
            data = res.json()
            print_test("POST /api/roadmap/generate", True, f"Generated roadmap '{data.get('job_role')}' with {data.get('total_tasks')} tasks.")
        else:
            print_test("POST /api/roadmap/generate", False, f"Status: {res.status_code} Body: {res.text}")
            
        # 6. Get Roadmap List
        print("\n--- 6. Get Roadmaps ---")
        res = client.get("/api/roadmap", headers=headers)
        if res.status_code == 200:
            data = res.json()
            if len(data) == 0:
                print_test("GET /api/roadmap", False, "No roadmap created in DB")
                return
            print_test("GET /api/roadmap", True, f"Found {len(data)} roadmaps.")
            rm_id = data[0].get('id')
        else:
            print_test("GET /api/roadmap", False, f"Status: {res.status_code} Body: {res.text}")
            return
            
        res_rm = client.get(f"/api/roadmap/{rm_id}", headers=headers)
        task_id = res_rm.json().get('tasks')[0].get('id')
            
        # 7. Complete Task
        print("\n--- 7. Complete Task ---")
        res = client.post(f"/api/roadmap/tasks/{task_id}/complete", headers=headers, json={"feedback_score": 4})
        if res.status_code == 200:
            res_rm2 = client.get(f"/api/roadmap/{rm_id}", headers=headers).json()
            completed = res_rm2.get('completed_tasks')
            
            # Find task
            task_status = [t for t in res_rm2.get('tasks') if t['id'] == task_id][0]['status']
            
            if completed == 1 and task_status == 'completed':
                print_test("POST /api/roadmap/tasks/{id}/complete", True, f"Task successfully marked completed. Roadmap completion: {completed}/{res_rm2.get('total_tasks')}")
            else:
                print_test("POST /api/roadmap/tasks/{id}/complete", False, "Task completion count failed to increment properly")
        else:
            print_test("POST /api/roadmap/tasks/{id}/complete", False, f"Status: {res.status_code} Body: {res.text}")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
