import csv
import os
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

BACKGROUND_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BACKGROUND_DIR / ".env"
DATA_DIR = BACKGROUND_DIR / "data"

load_dotenv(ENV_PATH)
DATABASE_URL = os.getenv("DATABASE_URL")

NEW_ROLES = [
    "Backend Developer", "Full Stack Developer", "Mobile App Developer",
    "Machine Learning Engineer", "Data Analyst", "Cloud Engineer",
    "QA/Test Engineer", "IoT Engineer", "NLP Engineer"
]

def main():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    cur = conn.cursor()

    csv_path = DATA_DIR / "job_skill_requirements.csv"
    data = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['job_role'] in NEW_ROLES:
                data.append((
                    row['id'],
                    row['job_role'],
                    row['skill_id'],
                    row['importance'],
                    float(row['min_score_required'])
                ))
    
    execute_values(
        cur,
        """
        INSERT INTO job_skill_requirements (id, job_role, skill_id, importance, min_score_required)
        VALUES %s
        ON CONFLICT (job_role, skill_id) DO NOTHING
        RETURNING job_role
        """,
        data,
        template="(%s::uuid, %s, %s::uuid, %s, %s)"
    )
    
    inserted = cur.fetchall()
    conn.commit()
    
    counts = {}
    for role in NEW_ROLES:
        counts[role] = 0
    for row in inserted:
        role = row[0]
        counts[role] = counts.get(role, 0) + 1
        
    for role in NEW_ROLES:
        print(f"Inserted {counts[role]} skill requirements for {role}")
        
    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
