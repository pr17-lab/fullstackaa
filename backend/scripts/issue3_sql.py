import os
import psycopg2
from dotenv import load_dotenv

load_dotenv("backend/.env")
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

print("Updating AIML target roles preference...")
cur.execute("""
UPDATE student_preferences sp
SET target_roles = CASE
  WHEN random() < 0.25 THEN ARRAY['Data Scientist', 'Machine Learning Engineer']
  WHEN random() < 0.45 THEN ARRAY['Machine Learning Engineer', 'NLP Engineer']
  WHEN random() < 0.60 THEN ARRAY['Data Scientist', 'Data Analyst']
  WHEN random() < 0.72 THEN ARRAY['Data Engineer', 'Data Scientist']
  WHEN random() < 0.82 THEN ARRAY['Backend Developer', 'Software Engineer']
  ELSE ARRAY['Full Stack Developer', 'Data Scientist']
END
WHERE sp.user_id IN (
  SELECT u.id FROM users u
  JOIN student_profiles p ON p.user_id = u.id
  WHERE p.department = 'AIML'
);
""")
print(f"AIML Student Preferences Updated. Rows Affected: {cur.rowcount}")

print("Updating CSE target roles preference...")
cur.execute("""
UPDATE student_preferences sp
SET target_roles = CASE
  WHEN random() < 0.15 THEN ARRAY['Software Engineer', 'Backend Developer']
  WHEN random() < 0.28 THEN ARRAY['Backend Developer', 'Full Stack Developer']
  WHEN random() < 0.40 THEN ARRAY['Full Stack Developer', 'Frontend Developer']
  WHEN random() < 0.52 THEN ARRAY['Data Scientist', 'Machine Learning Engineer']
  WHEN random() < 0.62 THEN ARRAY['Data Engineer', 'Data Analyst']
  WHEN random() < 0.70 THEN ARRAY['DevOps Engineer', 'Cloud Engineer']
  WHEN random() < 0.78 THEN ARRAY['Cybersecurity Analyst', 'Backend Developer']
  WHEN random() < 0.85 THEN ARRAY['QA/Test Engineer', 'Software Engineer']
  WHEN random() < 0.92 THEN ARRAY['Data Analyst', 'Data Scientist']
  ELSE ARRAY['Technical Product Manager', 'Backend Developer']
END
WHERE sp.user_id IN (
  SELECT u.id FROM users u
  JOIN student_profiles p ON p.user_id = u.id
  WHERE p.department = 'CSE'
);
""")
print(f"CSE Student Preferences Updated. Rows Affected: {cur.rowcount}")

conn.commit()
cur.close()
conn.close()
