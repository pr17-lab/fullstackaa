from app.core.database import SessionLocal
from app.models.roadmap import RoadmapTask

def undo():
    db = SessionLocal()
    try:
        tasks = db.query(RoadmapTask).filter(RoadmapTask.task_type != 'custom').all()
        fixes = 0
        for task in tasks:
            if "Learn" in task.title:
                task.phase = "learn"
                task.task_type = "course"
                fixes += 1
            elif "Practice" in task.title:
                task.phase = "practice"
                task.task_type = "exercise"
                fixes += 1
            elif "Build" in task.title:
                task.phase = "apply"
                task.task_type = "project"
                fixes += 1
        
        db.commit()
        print(f"Fixed {fixes} tasks based on their titles.")
    except Exception as e:
        print("Error:", e)
    finally:
        db.close()

if __name__ == "__main__":
    undo()
