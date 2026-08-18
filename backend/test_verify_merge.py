"""
test_verify_merge.py — Post-merge verification script.
Run inside Docker: docker exec student-tracker-api python test_verify_merge.py
"""
import asyncio
import os
import time

# ============================================================
# TEST 3: Static bank fallback (both APIs disabled)
# ============================================================
print("=== TEST 3: Tier 3 (Static Bank Fallback) ===")
from app.core import config as cfg
cfg.settings.GROQ_API_KEY = ""
cfg.settings.GEMINI_API_KEY = ""

from app.modules.interview.service import InterviewService
svc = InterviewService()

t0 = time.time()
questions, tier = asyncio.run(svc.generate_questions_async(
    branch="CSE",
    semester=6,
    jd_text="Some JD text",
    limit=5,
))
elapsed = time.time() - t0
print(f"Tier used: {tier}")
print(f"Questions returned: {len(questions)}")
print(f"Generation time: {elapsed:.4f}s (should be near-instant)")
print(f"Sample topic: {questions[0].get('topic') if questions else 'N/A'}")
assert tier == "static_fallback", f"Expected static_fallback, got {tier}"
assert len(questions) > 0, "Static bank returned no questions"
print("PASS: Static fallback works correctly\n")

# ============================================================
# TEST 4: Real-time evaluation (Gemini eval path)
# ============================================================
print("=== TEST 4: evaluate_single_answer_async (Gemini eval) ===")
cfg.settings.GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
cfg.settings.GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

from app.core.database import SessionLocal
from app.models.user import User
from app.models.interview import InterviewSession, InterviewQuestion, SessionStatus

db = SessionLocal()
user = db.query(User).filter(User.student_id == "S2026001").first()
print(f"Testing as: {user.email}")

# Use create_session (does NOT include is_micro/associated_skill_id/roadmap_task_id)
test_questions = [
    {"topic": "Data Structures", "question": "Explain stack vs queue.", "difficulty": "medium"},
]
session = svc.create_session(
    db,
    user_id=user.id,
    branch="CSE",
    topic="Test",
    questions=test_questions,
)

# Get the created question
question = db.query(InterviewQuestion).filter(InterviewQuestion.session_id == session.id).first()

ANSWER = "A stack uses LIFO. Queue uses FIFO. Stack used in recursion, queue used in BFS."

t0 = time.time()
result = asyncio.run(svc.evaluate_single_answer_async(
    db,
    user_id=user.id,
    session_id=session.id,
    question_id=question.id,
    user_answer=ANSWER,
))
elapsed = time.time() - t0

print(f"Evaluation time: {elapsed:.2f}s")
print(f"technical_score: {result.get('technical_score')}")
print(f"verdict: {result.get('verdict')}")
feedback = str(result.get("feedback", ""))
print(f"feedback (first 100 chars): {feedback[:100]}")
print(f"confidence_score: {result.get('confidence_score')}")

assert result.get("technical_score") is not None, f"technical_score missing — result keys: {list(result.keys())}"
assert result.get("verdict") in ("Strong", "Adequate", "Weak"), f"Unexpected verdict: {result.get('verdict')}"
print("PASS: Evaluation (technical_score, verdict, feedback) all present\n")

# ============================================================
# TEST 5: groq_client.py importable at new path
# ============================================================
print("=== TEST 5: groq_client.py import at new path ===")
import app.modules.interview.groq_client as gc
assert callable(gc.generate_questions_with_groq), "generate_questions_with_groq not callable"
print("PASS: app.modules.interview.groq_client imports correctly\n")

db.close()
print("=== ALL TESTS PASSED ===")
