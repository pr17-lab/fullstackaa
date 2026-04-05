import asyncio
import logging
from app.modules.interview.service import interview_service
from decimal import Decimal

logging.basicConfig(level=logging.DEBUG)

async def test():
    jd = "We are hiring a React Frontend Developer. Required skills: React, TypeScript, CSS, REST APIs, Git"
    # Using dummy args matching service signature
    questions, source = await interview_service.generate_questions_async(
        branch="CSE",
        semester=6,
        weak_subjects=[],
        overall_gpa=Decimal("8.5"),
        jd_text=jd,
        resume_context="",
        limit=5
    )
    print("Source:", source)
    print("Questions:")
    for i, q in enumerate(questions):
        print(f"{i+1}. [{q.get('topic')}] {q.get('difficulty')} - {q.get('question')}")

if __name__ == "__main__":
    asyncio.run(test())
