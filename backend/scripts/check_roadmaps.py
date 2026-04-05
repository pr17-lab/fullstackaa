import json
from app.core.database import SessionLocal
from app.models.roadmap import RoadmapTask, Roadmap

def check():
    db = SessionLocal()
    # Get the latest active roadmap
    r = db.query(Roadmap).order_by(Roadmap.created_at.desc()).first()
    print(f"Roadmap: {r.id} {r.job_role}")
    
    tasks = db.query(RoadmapTask).filter(RoadmapTask.roadmap_id == r.id).order_by(RoadmapTask.created_at, RoadmapTask.order_index).all()
    for t in tasks:
        print(f"[{t.order_index}] {t.phase} ({t.task_type}) - {t.title}")
        
    db.close()

if __name__ == "__main__":
    check()
