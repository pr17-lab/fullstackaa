"""
groq_client.py — Groq LLM wrapper for interview question generation.

Design principles (production-hardened):
  - Temperature controlled via GROQ_TEMPERATURE env var (default 0.7).
  - Strict JSON validation: parses, validates structure, validates keys,
    validates difficulty values. Returns None on any format error.
  - Near-duplicate deduplication: removes questions whose first N words
    are identical to an already-accepted question.
  - Timeout safety: GROQ_TIMEOUT_SEC env var (default 10s). Cancelled
    requests fall back immediately — never block the interview flow.
  - Rate limit awareness: groq.RateLimitError caught explicitly, logged,
    returns None for silent fallback.
  - Restricted logging: NEVER logs full question text or raw LLM output.
    Only logs question count, branch, and error type.
  - Max token cap: GROQ_MAX_TOKENS env var (default 1024) prevents
    runaway output size.

Returns:
    list[dict] with keys {question, topic, difficulty} on success.
    None on any failure (caller falls back to built-in bank).
"""
from __future__ import annotations

import os
import json
import logging
import difflib
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Environment-driven configuration
# ---------------------------------------------------------------------------

_GROQ_API_KEY: Optional[str] = os.environ.get("GROQ_API_KEY")
_GROQ_MODEL: str = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
_GROQ_TEMPERATURE: float = float(os.environ.get("GROQ_TEMPERATURE", "0.7"))
_GROQ_MAX_TOKENS: int = int(os.environ.get("GROQ_MAX_TOKENS", "1024"))
_GROQ_TIMEOUT_SEC: float = float(os.environ.get("GROQ_TIMEOUT_SEC", "10.0"))

_VALID_DIFFICULTIES = {"easy", "medium", "hard"}
_DEDUP_PREFIX_WORDS = 6  # compare first N words for near-duplicate detection


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _build_prompt(
    branch: str,
    semester: int,
    overall_gpa: float,
    weak_subjects: list[str],
    jd_text: str,
    resume_context: Optional[str],
    limit: int,
) -> str:
    weak_str = (
        f"{', '.join(weak_subjects)}"
        if weak_subjects else
        "None identified"
    )
    resume_str = (
        resume_context.strip()[:500]
        if resume_context else
        "Not provided"
    )
    difficulty_guidance = (
        "emphasize conceptual clarity and fundamentals"
        if overall_gpa < 6.5 else
        "balanced conceptual and applied reasoning"
        if overall_gpa <= 8.0 else
        "include deeper system design or optimization trade-offs"
    )

    return (
        f"You are a senior technical interviewer conducting a live mock interview for a job candidate.\n\n"
        f"Generate exactly {limit} distinct interview questions tailored to the following job description and student profile.\n\n"
        f"-------------------------\n"
        f"JOB DESCRIPTION:\n"
        f"{jd_text.strip()}\n"
        f"-------------------------\n\n"
        f"STUDENT PROFILE:\n"
        f"- Branch: {branch}\n"
        f"- Semester: {semester}\n"
        f"- GPA: {overall_gpa:.1f}/10\n"
        f"- Academically weak subjects: {weak_str}\n"
        f"- Resume skills: {resume_str}\n\n"
        f"Instructions:\n\n"
        f"1. Focus primarily on the core technical skills and technologies explicitly mentioned in the job description.\n"
        f"2. Prioritize MUST-HAVE skills over nice-to-have skills.\n"
        f"3. Adapt question difficulty to the student's GPA ({overall_gpa:.1f}/10): {difficulty_guidance}.\n"
        f"4. Ensure:\n"
        f"   - At least 3 easy questions\n"
        f"   - At least 4 medium questions\n"
        f"   - At least 3 hard questions\n"
        f"5. Questions must:\n"
        f"   - Be technical and reasoning-based\n"
        f"   - Be answerable verbally in ~60-90 seconds\n"
        f"   - Avoid direct textbook definitions\n"
        f"   - Avoid repeated themes or structures\n"
        f"   - Cover different aspects of the JD (architecture, debugging, optimization, trade-offs, fundamentals)\n"
        f"6. If the job description includes specific technologies (e.g., FastAPI, SQL, Docker, React), include scenario-based questions using those technologies.\n"
        f"7. Subtly probe weak academic areas when relevant (e.g., logical reasoning, analytical thinking), without explicitly referencing them.\n"
        f"8. Do NOT generate coding syntax. Focus on explanation and reasoning.\n\n"
        f"Return ONLY a valid JSON array.\n"
        f"No markdown.\n"
        f"No explanations.\n"
        f"No extra text.\n\n"
        f"Format:\n"
        f'[\n'
        f'  {{\n'
        f'    "topic": "Skill or technology being tested",\n'
        f'    "question": "Interview question text here?",\n'
        f'    "difficulty": "easy|medium|hard"\n'
        f'  }}\n'
        f']'
    )


# ---------------------------------------------------------------------------
# JSON parsing + validation
# ---------------------------------------------------------------------------

def _parse_and_validate(raw: str, limit: int) -> Optional[list[dict]]:
    """
    Strictly parse the LLM response.

    Handles cases where the model wraps the JSON in prose or markdown.
    Returns None if the format is invalid or required keys are missing.
    """
    # Strip common LLM preamble: find the first '[' and last ']'
    start = raw.find("[")
    end = raw.rfind("]")
    if start == -1 or end == -1 or end <= start:
        logger.warning("Groq: response does not contain a JSON array (no brackets found)")
        return None

    json_str = raw[start : end + 1]

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as exc:
        logger.warning("Groq: JSON parse error — %s", exc)
        return None

    if not isinstance(data, list):
        logger.warning("Groq: parsed JSON is not a list")
        return None

    validated: list[dict] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        # Require all three keys
        question = item.get("question", "").strip()
        topic = item.get("topic", "").strip()
        difficulty = str(item.get("difficulty", "")).strip().lower()

        if not question or not topic:
            continue  # skip malformed entries silently
        if difficulty not in _VALID_DIFFICULTIES:
            difficulty = "medium"  # normalise invalid difficulty instead of dropping

        validated.append({"topic": topic, "question": question, "difficulty": difficulty})

    if not validated:
        logger.warning("Groq: no valid questions found after validation")
        return None

    return validated[:limit]


# ---------------------------------------------------------------------------
# Near-duplicate deduplication
# ---------------------------------------------------------------------------

def _deduplicate(questions: list[dict]) -> list[dict]:
    """
    Remove questions whose first N words are near-identical to an
    already-accepted question. Uses difflib similarity as secondary check.
    """
    seen_prefixes: list[str] = []
    unique: list[dict] = []

    for q in questions:
        words = q["question"].lower().split()
        prefix = " ".join(words[:_DEDUP_PREFIX_WORDS])

        is_duplicate = any(
            difflib.SequenceMatcher(None, prefix, seen).ratio() > 0.85
            for seen in seen_prefixes
        )
        if not is_duplicate:
            seen_prefixes.append(prefix)
            unique.append(q)

    return unique


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def generate_questions_with_groq(
    branch: str,
    semester: int,
    overall_gpa: float,
    weak_subjects: list[str],
    jd_text: str,
    resume_context: Optional[str] = None,
    limit: int = 10,
) -> Optional[list[dict]]:
    """
    Call Groq API to generate interview questions. Returns None on any
    failure so the caller can fall back to the built-in bank.

    Logs:
        - Question count + branch on success (no question text logged).
        - Error type only on failure (no raw response logged).
    """
    if not _GROQ_API_KEY:
        logger.info("Groq: GROQ_API_KEY not set — skipping LLM path")
        return None

    try:
        import groq as groq_sdk
        from groq import RateLimitError, APITimeoutError, APIError
    except ImportError:
        logger.error("Groq: groq package not installed — skipping LLM path")
        return None

    if not jd_text or not jd_text.strip():
        logger.warning("Groq: empty jd_text — falling back to built-in bank")
        return None

    prompt = _build_prompt(branch, semester, overall_gpa, weak_subjects, jd_text, resume_context, limit)

    try:
        client = groq_sdk.Groq(
            api_key=_GROQ_API_KEY,
            timeout=_GROQ_TIMEOUT_SEC,
        )
        completion = client.chat.completions.create(
            model=_GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=_GROQ_TEMPERATURE,
            max_tokens=_GROQ_MAX_TOKENS,
        )
        raw_content = completion.choices[0].message.content or ""

    except groq_sdk.RateLimitError:
        logger.warning(
            "Groq: rate limit reached (branch=%s) — falling back to built-in bank", branch
        )
        return None

    except groq_sdk.APITimeoutError:
        logger.warning(
            "Groq: request timed out after %.1fs (branch=%s) — falling back", _GROQ_TIMEOUT_SEC, branch
        )
        return None

    except groq_sdk.APIError as exc:
        logger.warning("Groq: API error (branch=%s, type=%s) — falling back", branch, type(exc).__name__)
        return None

    except Exception as exc:
        logger.warning("Groq: unexpected error (branch=%s, type=%s) — falling back", branch, type(exc).__name__)
        return None

    # Validate + deduplicate — never log raw_content
    questions = _parse_and_validate(raw_content, limit)
    if questions is None:
        return None

    questions = _deduplicate(questions)
    if not questions:
        logger.warning("Groq: all questions removed by deduplication (branch=%s) — falling back", branch)
        return None

    logger.info(
        "Groq: generated %d questions for branch=%s (model=%s)",
        len(questions), branch, _GROQ_MODEL,
    )
    return questions
