"""
Shared academic calculation utilities.
Used by the auth registration flow and any future grading logic.
"""


def calculate_grade(marks: int | None) -> str | None:
    """Convert a raw mark to a letter grade (O/A+/A/B+/B/C/D/F)."""
    if marks is None:
        return None
    if marks >= 90: return "O"
    if marks >= 80: return "A+"
    if marks >= 70: return "A"
    if marks >= 60: return "B+"
    if marks >= 50: return "B"
    if marks >= 45: return "C"
    if marks >= 40: return "D"
    return "F"


def calculate_grade_points(grade: str | None) -> int:
    """Return the grade-point value (0–10) for a letter grade."""
    gp = {"O": 10, "A+": 9, "A": 8, "B+": 7, "B": 6, "C": 5, "D": 4, "F": 0}
    return gp.get(grade, 0)


def score_to_level(score: float) -> str:
    """Map a 0–100 confidence score to a skill level label."""
    if score >= 80:
        return "strong"
    if score >= 50:
        return "moderate"
    return "weak"
