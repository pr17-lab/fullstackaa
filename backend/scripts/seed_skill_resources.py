import os
import sys
from sqlalchemy.orm import Session
from uuid import UUID

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

from app.core.database import SessionLocal
from app.models.skill_taxonomy import SkillTaxonomy
from app.models.skill_resource import SkillResource

RES_MAP = {
    "DSA": {"url": "https://www.coursera.org/learn/algorithms-part1", "platform": "Coursera", "hours": 20},
    "Python": {"url": "https://www.coursera.org/learn/python", "platform": "Coursera", "hours": 15},
    "Machine Learning": {"url": "https://www.coursera.org/learn/machine-learning", "platform": "Coursera", "hours": 30},
    "Deep Learning": {"url": "https://www.coursera.org/specializations/deep-learning", "platform": "Coursera", "hours": 25},
    "SQL": {"url": "https://www.kaggle.com/learn/intro-to-sql", "platform": "Kaggle", "hours": 10},
    "PostgreSQL": {"url": "https://www.kaggle.com/learn/intro-to-sql", "platform": "Kaggle", "hours": 10},
    "DBMS": {"url": "https://www.kaggle.com/learn/intro-to-sql", "platform": "Kaggle", "hours": 10},
    "Docker": {"url": "https://www.udemy.com/course/docker-mastery", "platform": "Udemy", "hours": 12},
    "AWS": {"url": "https://www.coursera.org/learn/aws-fundamentals", "platform": "Coursera", "hours": 20},
    "Git": {"url": "https://www.udemy.com/course/git-complete", "platform": "Udemy", "hours": 8},
    "React": {"url": "https://www.coursera.org/learn/front-end-react", "platform": "Coursera", "hours": 20},
    "System Design": {"url": "https://www.educative.io/courses/grokking-the-system-design-interview", "platform": "Educative", "hours": 15},
    "CAD Design": {"url": "https://www.coursera.org/learn/autodesk-cad", "platform": "Coursera", "hours": 20},
    "Strength of Materials": {"url": "https://www.coursera.org/learn/mechanics-1", "platform": "Coursera", "hours": 25},
    "Manufacturing Processes": {"url": "https://www.coursera.org/learn/advanced-manufacturing", "platform": "Coursera", "hours": 15},
    "Thermodynamics": {"url": "https://www.coursera.org/learn/thermodynamics", "platform": "Coursera", "hours": 20},
    "Heat Transfer": {"url": "https://www.coursera.org/learn/heat-transfer", "platform": "Coursera", "hours": 18},
    "Fluid Mechanics": {"url": "https://www.coursera.org/learn/fluid-mechanics", "platform": "Coursera", "hours": 20},
}

PRAC_MAP = {
    "DSA": {"url": "https://leetcode.com/study-plan/data-structure", "platform": "LeetCode", "hours": 10},
    "Machine Learning": {"url": "https://www.kaggle.com/competitions", "platform": "Kaggle", "hours": 8},
    "Deep Learning": {"url": "https://www.kaggle.com/competitions", "platform": "Kaggle", "hours": 8},
    "Data Analysis": {"url": "https://www.kaggle.com/competitions", "platform": "Kaggle", "hours": 8},
    "SQL": {"url": "https://leetcode.com/problemset/database", "platform": "LeetCode", "hours": 6},
    "CAD Design": {"url": "https://grabcad.com/library", "platform": "GrabCAD", "hours": 10},
    "Strength of Materials": {"url": "https://www.engineeringtoolbox.com/", "platform": "EngToolbox", "hours": 8},
    "Manufacturing Processes": {"url": "https://ocw.mit.edu/courses/mechanical-engineering/", "platform": "MIT OCW", "hours": 8},
    "Thermodynamics": {"url": "https://ocw.mit.edu/courses/mechanical-engineering/", "platform": "MIT OCW", "hours": 10},
    "Heat Transfer": {"url": "https://ocw.mit.edu/courses/mechanical-engineering/", "platform": "MIT OCW", "hours": 8},
    "Fluid Mechanics": {"url": "https://ocw.mit.edu/courses/mechanical-engineering/", "platform": "MIT OCW", "hours": 8},
}

def seed_resources():
    db: Session = SessionLocal()
    print("Seeding SkillResource map into database...")
    
    tax_items = db.query(SkillTaxonomy).all()
    count = 0
    for s in tax_items:
        sname = s.skill_name
        
        # Check Learn resource
        l_res = db.query(SkillResource).filter(SkillResource.skill_id == s.id, SkillResource.phase == "learn").first()
        if not l_res and sname in RES_MAP:
            data = RES_MAP[sname]
            nr = SkillResource(skill_id=s.id, phase="learn", platform=data["platform"], resource_url=data["url"], estimated_hours=data["hours"])
            db.add(nr)
            count += 1
            
        p_res = db.query(SkillResource).filter(SkillResource.skill_id == s.id, SkillResource.phase == "practice").first()
        if not p_res and sname in PRAC_MAP:
            data = PRAC_MAP[sname]
            nr = SkillResource(skill_id=s.id, phase="practice", platform=data["platform"], resource_url=data["url"], estimated_hours=data["hours"])
            db.add(nr)
            count += 1
            
    db.commit()
    db.close()
    print(f"Successfully inserted {count} static records into skill_resources.")

if __name__ == "__main__":
    seed_resources()
