import asyncio
import os
import sys

# add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.modules.interview.service import interview_service

async def main():
    questions, source = await interview_service.generate_questions_async(
        branch="AIML",
        semester=6,
        weak_subjects=["Data Structures"],
        overall_gpa=8.5,
        jd_text="Experience in building web applications, designing RESTful APIs, Node.js, Python, NoSQL databases.",
        resume_context="None",
        limit=3
    )
    print("SOURCE:", source)
    for q in questions:
        print("Q:", q.get("question"))
        
if __name__ == "__main__":
    asyncio.run(main())
