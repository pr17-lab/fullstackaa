"""
Verify that student profiles were updated correctly.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://studentadmin:studentpass123@localhost:5432/student_tracker"
engine = create_engine(DATABASE_URL)

def verify():
    with open('verification_results.txt', 'w') as f:
        f.write("="*80 + "\n")
        f.write("VERIFYING PROFILE UPDATES\n")
        f.write("="*80 + "\n")
        
        with engine.connect() as conn:
            # Check S00004
            f.write("\n[1] Checking S00004 (Akhil Reddy)...\n")
            query = text("""
                SELECT sp.name, sp.branch, sp.semester, u.email 
                FROM student_profiles sp
                JOIN users u ON sp.user_id = u.id
                WHERE u.email LIKE 'akhil.reddy%'
            """)
            result = conn.execute(query).fetchone()
            
            if result:
                f.write(f"     Name:     {result[0]}\n")
                f.write(f"     Branch:   {result[1]}\n")
                f.write(f"     Semester: {result[2]}\n")
                f.write(f"     Email:    {result[3]}\n")
            else:
                f.write("     [FAIL] Could not find student 'akhil.reddy'\n")

            # Check Department Distribution
            f.write("\n[2] Checking Department Distribution:\n")
            dist_query = text("SELECT branch, COUNT(*) FROM student_profiles GROUP BY branch ORDER BY branch")
            dist_results = conn.execute(dist_query).fetchall()
            
            f.write(f"    {'Branch':<25} | {'Count'}\n")
            f.write(f"    {'-'*25}-+-{'-'*10}\n")
            for row in dist_results:
                f.write(f"    {row[0]:<25} | {row[1]}\n")
                
if __name__ == "__main__":
    verify()
