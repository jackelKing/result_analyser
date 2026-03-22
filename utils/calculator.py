from utils.db import get_credit
from utils.extractor import GRADE_POINTS

def compute_sgpa(grades: dict, credit_map: dict) -> tuple[float | None, list]:
    """
    grades     : {subject_code: letter_grade}
    credit_map : {subject_code: credits}   (from DB + user input)
    Returns (sgpa, missing_subjects)
    """
    total_points = 0
    total_credits = 0
    missing = []

    for subj, grade in grades.items():
        credits = credit_map.get(subj) or get_credit(subj)
        if credits is None:
            missing.append(subj)
            continue
        gp = GRADE_POINTS.get(grade, 0)
        total_points  += gp * credits
        total_credits += credits

    if total_credits == 0:
        return None, missing

    sgpa = round(total_points / total_credits, 2)
    return sgpa, missing

def compute_cgpa(sgpa_list: list[float | None]) -> float | None:
    valid = [s for s in sgpa_list if s is not None]
    if not valid:
        return None
    return round(sum(valid) / len(valid), 2)
