import subprocess
import time
import requests

proc = subprocess.Popen(
    ["python", "-m", "uvicorn", "app.main:app", "--port", "8001"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    cwd=r"C:\Users\Admin\Desktop\fullstack\backend"
)

time.sleep(4)
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzYW5qYXkua3VtYXIwMDFAY29sbGVnZS5lZHUiLCJ1c2VyX2lkIjoiMTA1NDdkM2YtYWQ5NS00NjI2LWEzNGMtZWFiZGU4N2Q1YTlhIiwic3R1ZGVudF9pZCI6IlMwMDAwMSIsImV4cCI6MTc3NDIxNTM1OX0.tsm9Z-MMWhxG0P9n9fXBy2HTUcZXBcTFf7mkAVGtNks"
try:
    requests.get("http://localhost:8001/api/auth/me", headers={"Authorization": f"Bearer {token}"})
except:
    pass

time.sleep(1)
proc.terminate()
outs, _ = proc.communicate(timeout=5)

with open("full_log.txt", "w") as f:
    f.write(outs)
