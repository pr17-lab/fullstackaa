import asyncio
import httpx
from pydantic import BaseModel

async def main():
    try:
        from app.core.config import settings
        from app.modules.interview.service import interview_service
        from decimal import Decimal
        
        # Test directly with empty JD but WITH resume to see if the else block triggers, OR test with JD.
        # Wait, the user said "still its asking generic cs questions" probably testing with a JD.
        jd = "We are hiring a React Frontend Developer. Required skills: React, TypeScript, CSS, REST APIs, Git"
        
        questions, source = await interview_service.generate_questions_async(
            branch='CSE',
            semester=6,
            weak_subjects=[],
            overall_gpa=Decimal('8.5'),
            jd_text=jd,
            resume_context='',
            limit=5
        )
        print("Source:", source)
        for i, q in enumerate(questions):
            print(f"[{q.get('topic')}] {q.get('question')}")
            
    except Exception as e:
        print("EXCEPTION:", type(e), e)

if __name__ == '__main__':
    asyncio.run(main())
