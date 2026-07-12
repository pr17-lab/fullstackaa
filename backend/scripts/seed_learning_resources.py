import os
import sys
from sqlalchemy.orm import Session
from uuid import UUID

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

from app.core.database import SessionLocal
from app.models.skill_taxonomy import SkillTaxonomy
from app.models.learning_resource import LearningResource

# Curated shortlist
CURATED_RESOURCES = {
    "React": [
        {"phase": "learn", "title": "React Official Documentation", "platform": "Official Docs", "url": "https://react.dev"},
        {"phase": "practice", "title": "React API Reference & Practice Hooks", "platform": "Official Reference", "url": "https://react.dev/reference/react"}
    ],
    "Python": [
        {"phase": "learn", "title": "Python Official Tutorial", "platform": "Official Tutorial", "url": "https://docs.python.org/3/tutorial/index.html"},
        {"phase": "practice", "title": "LeetCode Coding Practice", "platform": "LeetCode", "url": "https://leetcode.com"}
    ],
    "FastAPI": [
        {"phase": "learn", "title": "FastAPI Official Documentation", "platform": "Official Docs", "url": "https://fastapi.tiangolo.com"},
        {"phase": "practice", "title": "FastAPI Tutorial - User Guide", "platform": "Official Docs", "url": "https://fastapi.tiangolo.com/tutorial/"}
    ],
    "Git": [
        {"phase": "learn", "title": "Git Pro Book & Documentation", "platform": "Official Docs", "url": "https://git-scm.com/doc"},
        {"phase": "practice", "title": "Interactive Git Branching Tutorial", "platform": "Learn Git Branching", "url": "https://learngitbranching.js.org"}
    ],
    "PostgreSQL": [
        {"phase": "learn", "title": "PostgreSQL Documentation", "platform": "Official Docs", "url": "https://www.postgresql.org/docs/"},
        {"phase": "practice", "title": "PostgreSQL Exercises", "platform": "PGExercises", "url": "https://www.pgexercises.com"}
    ],
    "Docker": [
        {"phase": "learn", "title": "Docker Documentation & Getting Started", "platform": "Official Docs", "url": "https://docs.docker.com"},
        {"phase": "practice", "title": "Play with Docker Classroom", "platform": "Play with Docker", "url": "https://labs.play-with-docker.com"}
    ],
    "HTML": [
        {"phase": "learn", "title": "MDN HTML Guide", "platform": "MDN", "url": "https://developer.mozilla.org/en-US/docs/Web/HTML"},
        {"phase": "practice", "title": "W3Schools HTML Tutorial", "platform": "W3Schools", "url": "https://www.w3schools.com/html/"}
    ],
    "CSS": [
        {"phase": "learn", "title": "MDN CSS Guide", "platform": "MDN", "url": "https://developer.mozilla.org/en-US/docs/Web/CSS"},
        {"phase": "practice", "title": "CSS-Tricks Almanac & Guides", "platform": "CSS-Tricks", "url": "https://css-tricks.com"}
    ],
    "JavaScript": [
        {"phase": "learn", "title": "MDN JavaScript Guide", "platform": "MDN", "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript"},
        {"phase": "practice", "title": "The Modern JavaScript Tutorial", "platform": "JavaScript.info", "url": "https://javascript.info"}
    ],
    "TypeScript": [
        {"phase": "learn", "title": "TypeScript Documentation", "platform": "Official Docs", "url": "https://www.typescriptlang.org/docs/"},
        {"phase": "practice", "title": "TypeScript Interactive Playground", "platform": "TypeScript Playground", "url": "https://www.typescriptlang.org/play"}
    ],
    "SQL": [
        {"phase": "learn", "title": "W3Schools SQL Tutorial", "platform": "W3Schools", "url": "https://www.w3schools.com/sql/"},
        {"phase": "practice", "title": "SQLBolt Interactive Lessons", "platform": "SQLBolt", "url": "https://sqlbolt.com"}
    ],
    "DSA": [
        {"phase": "learn", "title": "Algorithms, Part I (Princeton)", "platform": "Coursera", "url": "https://www.coursera.org/learn/algorithms-part1"},
        {"phase": "practice", "title": "LeetCode DSA Study Plan", "platform": "LeetCode", "url": "https://leetcode.com/study-plan/data-structure"}
    ],
    "DBMS": [
        {"phase": "learn", "title": "Intro to SQL", "platform": "Kaggle", "url": "https://www.kaggle.com/learn/intro-to-sql"},
        {"phase": "practice", "title": "Database Practice Problems", "platform": "LeetCode", "url": "https://leetcode.com/problemset/database"}
    ],
    "Computer Networks": [
        {"phase": "learn", "title": "Computer Networks Lecture Notes", "platform": "MIT OCW", "url": "https://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-829-computer-networks-fall-2002/"},
        {"phase": "practice", "title": "Cisco Packet Tracer Tutorials", "platform": "PacketTracer", "url": "https://www.packettracer.info"}
    ],
    "Operating Systems": [
        {"phase": "learn", "title": "OSTEP Book (Operating Systems: Three Easy Pieces)", "platform": "OSTEP", "url": "http://pages.cs.wisc.edu/~remzi/OSTEP/"},
        {"phase": "practice", "title": "MIT xv6 Operating System Labs", "platform": "MIT xv6", "url": "https://pdos.csail.mit.edu/6.828/2020/xv6.html"}
    ]
}

def seed_learning_resources():
    db: Session = SessionLocal()
    print("Seeding curated learning resources...")
    count = 0
    for sname, resources in CURATED_RESOURCES.items():
        # Find skill in skill_taxonomy (using ilike for case insensitivity)
        skill = db.query(SkillTaxonomy).filter(SkillTaxonomy.skill_name.ilike(sname)).first()
        if not skill:
            print(f"Skill '{sname}' not found in taxonomy, skipping...")
            continue
        
        for rdata in resources:
            # Check if already exists
            existing = db.query(LearningResource).filter(
                LearningResource.skill_id == skill.id,
                LearningResource.phase == rdata["phase"],
                LearningResource.resource_url == rdata["url"]
            ).first()
            if not existing:
                lr = LearningResource(
                    skill_id=skill.id,
                    title=rdata["title"],
                    resource_url=rdata["url"],
                    platform=rdata["platform"],
                    phase=rdata["phase"],
                    upvotes=5,  # seed curated ones with initial trust score
                    downvotes=0
                )
                db.add(lr)
                count += 1
    db.commit()
    db.close()
    print(f"Seeding completed. Inserted {count} curated resources.")

if __name__ == "__main__":
    seed_learning_resources()
