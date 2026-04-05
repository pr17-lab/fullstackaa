import sys
from groq import Groq
import json
import os
from dotenv import load_dotenv

load_dotenv(".env")
key = os.getenv("GROQ_API_KEY")

client = Groq(api_key=key)
limit = 3
prompt = f"""You are a Senior Staff Engineer conducting a technical job interview.

JOB DESCRIPTION:
We are hiring a React Frontend Developer. Required skills: React, TypeScript, CSS, REST APIs, Git

TASK: Generate exactly {limit} interview questions based STRICTLY on the technical skills, tools, and responsibilities listed in the job description above. Do NOT ask generic CS or academic questions unrelated to the JD.

Student calibration (for difficulty only):
- Branch: Computer Science | Semester: 4 | GPA: 7.0/10
- Weak areas: none

CRITICAL RULES:
1. NO TRIVIA: Do not ask "What is X?" or "Define Y." Every question must be practical and applied.
2. SCENARIO-BASED: Prefer "How would you...", "Walk me through...", "What tradeoffs exist between...".
3. DIFFICULTY MIX: 1 easy (practical usage), 1 medium (troubleshooting/design), 1 hard (scale/edge-cases/architecture).
4. HYPER-SPECIFIC: Ground every question in a real technology or skill from the context.

Return ONLY a valid JSON array — no markdown, no explanation:
[
  {{"topic": "specific skill", "question": "scenario-based question text", "difficulty": "easy|medium|hard"}}
]"""

try:
    r = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=2000,
    )
    print("=== FINAL OUTPUT ===")
    print(r.choices[0].message.content)
except Exception as e:
    print("Error:", e)
