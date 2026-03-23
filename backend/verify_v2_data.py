import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def print_result(cur, query, title=""):
    print(f"\n{"="*50}\n{title}\n{"="*50}")
    cur.execute(query)
    # Check if this is a simple count:
    desc = [col[0] for col in cur.description]
    
    # If just one column and it's 'count'
    if len(desc) == 1 and desc[0] == 'count':
        print(f"COUNT: {cur.fetchone()[0]}")
        return
        
    # Otherwise print table
    # Print headers
    header = " | ".join(f"{col:<20}" for col in desc)
    print(header)
    print("-" * len(header))
    for row in cur.fetchall():
        print(" | ".join(f"{str(v):<20}" for v in row))

def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    print_result(cur, "SELECT COUNT(*) FROM skill_taxonomy;", "skill_taxonomy count")
    print_result(cur, "SELECT COUNT(*) FROM job_skill_requirements;", "job_skill_requirements count")
    print_result(cur, "SELECT COUNT(*) FROM student_preferences;", "student_preferences count")
    print_result(cur, "SELECT COUNT(*) FROM student_skills;", "student_skills count")
    print_result(cur, "SELECT COUNT(*) FROM skill_gaps;", "skill_gaps count")
    print_result(cur, "SELECT COUNT(*) FROM behavior_summary;", "behavior_summary count")

    q_avg_match = """
    SELECT job_role, 
           ROUND(AVG(match_score), 2) as avg_match,
           COUNT(*) as student_count
    FROM skill_gaps 
    GROUP BY job_role 
    ORDER BY avg_match DESC;
    """
    print_result(cur, q_avg_match, "Average match score per job role")

    q_skill_dist = """
    SELECT level, COUNT(*) 
    FROM student_skills 
    GROUP BY level;
    """
    print_result(cur, q_skill_dist, "Skill distribution")

    q_top10 = """
    SELECT st.skill_name, COUNT(*) as strong_count
    FROM student_skills ss
    JOIN skill_taxonomy st ON ss.skill_id = st.id
    WHERE ss.level = 'strong'
    GROUP BY st.skill_name
    ORDER BY strong_count DESC
    LIMIT 10;
    """
    print_result(cur, q_top10, "Top 10 strong skills")

    q_spot = """
    SELECT u.student_id, sp.department, sp.cgpa,
           ss.confidence_score, st.skill_name, ss.level
    FROM users u
    JOIN student_profiles sp ON sp.user_id = u.id
    JOIN student_skills ss ON ss.user_id = u.id
    JOIN skill_taxonomy st ON st.id = ss.skill_id
    WHERE u.student_id = 'S00001'
    ORDER BY ss.confidence_score DESC;
    """
    print_result(cur, q_spot, "Spot check S00001")

if __name__ == "__main__":
    main()
