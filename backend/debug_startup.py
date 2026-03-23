import subprocess, sys
result = subprocess.run(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8001"],
    capture_output=True, text=True, timeout=10,
    cwd=r"C:\Users\Admin\Desktop\fullstack\backend"
)
print("STDOUT:", result.stdout[-3000:] if result.stdout else "(empty)")
print("STDERR:", result.stderr[-3000:] if result.stderr else "(empty)")
print("Exit code:", result.returncode)
