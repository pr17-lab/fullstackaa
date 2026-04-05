import asyncio
from app.modules.interview.service import interview_service
from decimal import Decimal
import logging

logging.basicConfig(level=logging.INFO)

async def test():
    print("--- Testing with React JD ---")
    qs, source = await interview_service.generate_questions_async(
        branch="Computer Science",
        semester=6,
        weak_subjects=["Algorithms", "Data Structures"],
        overall_gpa=Decimal('8.5'),
        jd_text="We are hiring a React Frontend Developer. Required skills: React, TypeScript, CSS, REST APIs, Git",
        resume_context="",
        limit=3
    )
    print(f"\n✅ Result Source: {source}")
    for i, q in enumerate(qs, 1):
        print(f"  Q{i} [{q.get('difficulty')}]: {q.get('question')} (Topic: {q.get('topic')})")

    print("\n--- Testing without JD (No JD/Resume context) ---")
    qs2, source2 = await interview_service.generate_questions_async(
        branch="Electronics",
        semester=4,
        weak_subjects=["Signals and Systems"],
        overall_gpa=Decimal('7.0'),
        limit=3
    )
    print(f"\n✅ Result Source: {source2}")
    for i, q in enumerate(qs2, 1):
        print(f"  Q{i} [{q.get('difficulty')}]: {q.get('question')} (Topic: {q.get('topic')})")

if __name__ == "__main__":
    asyncio.run(test())
