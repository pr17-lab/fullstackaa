import os
import psycopg2
from dotenv import load_dotenv

load_dotenv("backend/.env")
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

query = """
SELECT sp.department, sg.job_role, COUNT(*) as students,
       ROUND(AVG(sg.match_score), 1) as avg_score
FROM skill_gaps sg
JOIN users u ON u.id = sg.user_id
JOIN student_profiles sp ON sp.user_id = u.id
GROUP BY sp.department, sg.job_role
ORDER BY sp.department, avg_score DESC;
"""

cur.execute(query)
rows = cur.fetchall()

print(f"{'Department':<12} | {'Job Role':<35} | {'Students':<10} | {'Avg Score':<10}")
print("-" * 75)
for row in rows:
    print(f"{row[0]:<12} | {row[1]:<35} | {row[2]:<10} | {row[3]:<10}")

cur.close()
conn.close()
