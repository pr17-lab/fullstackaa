import os
import psycopg2
from dotenv import load_dotenv

load_dotenv("backend/.env")
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

query1 = """
SELECT sp.department, sg.job_role, COUNT(*) as students,
       ROUND(AVG(sg.match_score), 1) as avg_score
FROM skill_gaps sg
JOIN users u ON u.id = sg.user_id
JOIN student_profiles sp ON sp.user_id = u.id
GROUP BY sp.department, sg.job_role
ORDER BY sp.department, avg_score DESC;
"""

cur.execute(query1)
rows1 = cur.fetchall()

with open("backend/scripts/final_report_utf8.txt", "w", encoding="utf-8") as f:
    f.write("--- OVERALL STATS ---\n")
    f.write(f"{'Department':<12} | {'Job Role':<35} | {'Students':<10} | {'Avg Score':<10}\n")
    f.write("-" * 75 + "\n")
    for row in rows1:
        f.write(f"{row[0]:<12} | {row[1]:<35} | {row[2]:<10} | {row[3]:<10}\n")

    f.write("\n\n--- TOP RECOMMENDED ROLE PER DEPARTMENT ---\n")
    query2 = """
    SELECT DISTINCT ON (sp.department) 
           sp.department, sg.job_role, 
           ROUND(AVG(sg.match_score), 1) as avg_score
    FROM skill_gaps sg
    JOIN users u ON u.id = sg.user_id
    JOIN student_profiles sp ON sp.user_id = u.id
    GROUP BY sp.department, sg.job_role
    ORDER BY sp.department, avg_score DESC;
    """

    cur.execute(query2)
    rows2 = cur.fetchall()
    f.write(f"{'Department':<12} | {'Job Role':<35} | {'Avg Score':<10}\n")
    f.write("-" * 65 + "\n")
    for row in rows2:
        f.write(f"{row[0]:<12} | {row[1]:<35} | {row[2]:<10}\n")

cur.close()
conn.close()
