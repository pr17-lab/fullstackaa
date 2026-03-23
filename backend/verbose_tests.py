import traceback, sys

try:
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    
    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    
    def print_test(name, passed, details=""):
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {name}")
        if details:
            print(f"       {details}")

    # 1. Login
    print("\n--- 1. Login ---")
    res = client.post('/api/auth/login', data={'username': 'S00001', 'password': 'S00001@123'})
    if res.status_code == 200:
        token = res.json().get("access_token")
        print_test("POST /api/auth/login", True, "Acquired JWT token")
    else:
        print_test("POST /api/auth/login", False, f"{res.status_code}: {res.text[:200]}")

    headers = {"Authorization": f"Bearer {token}"}

    # 2
    print("\n--- 2. Skills Summary ---")
    res = client.get("/api/skills/summary", headers=headers)
    if res.status_code == 200:
        d = res.json()
        print_test("GET /api/skills/summary", True, f"total_skills={d['total_skills']} strong={d['strong_count']} moderate={d['moderate_count']} weak={d['weak_count']} top5={[s['skill_name'] for s in d['top_skills']]}")
    else:
        print_test("GET /api/skills/summary", False, f"{res.status_code}: {res.text[:300]}")

    # 3
    print("\n--- 3. Skills Gaps ---")
    res = client.get("/api/skills/gaps", headers=headers)
    if res.status_code == 200:
        d = res.json()
        print_test("GET /api/skills/gaps", True, f"Returned {len(d)} gaps")
        for g in d:
            print(f"         {g['job_role']}: score={g['match_score']:.1f}% label={g['match_label']}")
    else:
        print_test("GET /api/skills/gaps", False, f"{res.status_code}: {res.text[:300]}")

    # 4
    print("\n--- 4. Preferences ---")
    res = client.get("/api/preferences", headers=headers)
    if res.status_code == 200:
        d = res.json()
        print_test("GET /api/preferences", True, f"target_roles={d['target_roles']}")
    else:
        print_test("GET /api/preferences", False, f"{res.status_code}: {res.text[:300]}")

    # 5
    print("\n--- 5. Generate Roadmap ---")
    res = client.post("/api/roadmap/generate", headers=headers, json={"job_role": "Data Scientist"})
    if res.status_code == 200:
        d = res.json()
        print_test("POST /api/roadmap/generate", True, f"job_role={d['job_role']} total_tasks={d['total_tasks']}")
        phases = {}
        for t in d['tasks']:
            phases.setdefault(t['phase'], []).append(t['title'])
        for ph, titles in phases.items():
            print(f"         Phase '{ph}': {len(titles)} tasks")
    else:
        print_test("POST /api/roadmap/generate", False, f"{res.status_code}: {res.text[:400]}")

    # 6
    print("\n--- 6. List Roadmaps ---")
    res = client.get("/api/roadmap", headers=headers)
    if res.status_code == 200:
        d = res.json()
        print_test("GET /api/roadmap", True, f"Found {len(d)} roadmap(s)")
        rm_id = d[0]['id']
    else:
        print_test("GET /api/roadmap", False, f"{res.status_code}: {res.text[:300]}")
        sys.exit(1)

    res_rm = client.get(f"/api/roadmap/{rm_id}", headers=headers)
    task_id = res_rm.json()['tasks'][0]['id']
    task_title = res_rm.json()['tasks'][0]['title']
    print(f"       First task: '{task_title}' (id={task_id})")

    # 7
    print("\n--- 7. Complete Task ---")
    res = client.post(f"/api/roadmap/tasks/{task_id}/complete", headers=headers, json={"feedback_score": 4})
    if res.status_code == 200:
        rm2 = client.get(f"/api/roadmap/{rm_id}", headers=headers).json()
        ct = rm2['completed_tasks']
        tt = rm2['total_tasks']
        task_st = next(t for t in rm2['tasks'] if t['id'] == task_id)['status']
        ok = (ct == 1 and task_st == 'completed')
        print_test("POST /api/roadmap/tasks/{id}/complete", ok,
                   f"task.status={task_st} completed_tasks={ct}/{tt}")
    else:
        print_test("POST /api/roadmap/tasks/{id}/complete", False, f"{res.status_code}: {res.text[:300]}")

    print("\n=== Done ===")

except Exception as e:
    tb = traceback.format_exc()
    with open('err2.txt', 'w', encoding='utf-8') as f:
        f.write(tb)
    print(tb)
