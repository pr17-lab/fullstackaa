import asyncio
from app.core.database import SessionLocal
from app.models.user import User
from app.modules.interview.router import create_session
from app.schemas.interview import SessionCreateRequest

async def main():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "kiran.iyer001").first()
        if not user:
            print("User not found!")
            return

        body = SessionCreateRequest(
            jd_text="React Developer typescript css",
            resume_context="",
            limit=3
        )

        session = await create_session(body=body, current_user=user, db=db)
        print("Session ID:", session.id)
        for q in session.questions:
            print(f"[{q.source}] {q.question}")
    except Exception as e:
        print("Exception:", type(e), e)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
