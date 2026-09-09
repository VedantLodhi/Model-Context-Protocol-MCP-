import re


ALGEBRA_PATTERNS = [
    r"\bsolve\b",
    r"\bequation\b",
    r"\balgebra\b",
    r"\bx\^",
    r"\bx\s*[+\-*/=]",
    r"[+\-*/=]\s*x\b",
]


UNIT_PATTERNS = [
    r"\bconvert\b",
    r"\bconversion\b",
    r"\bto\b.*\b(?:km|kilometers?|miles?|meters?|kg|kilograms?|pounds?|lbs?|grams?|feet|foot|inches?|cm|mm)\b",
    r"\b(?:km|kilometers?|miles?|meters?|kg|kilograms?|pounds?|lbs?|grams?|feet|foot|inches?|cm|mm)\b.*\bto\b",
    r"\b(?:km|kilometers?|miles?|meters?|kg|kilograms?|pounds?|lbs?|grams?|feet|foot|inches?|cm|mm)\b.*\b(?:into|in)\b",
    r"\b(?:degrees?\s*c|degrees?\s*f)\b.*\b(?:to|into|in)\b",
]


DATETIME_PATTERNS = [
    r"\bwhat time\b",
    r"\bcurrent time\b",
    r"\btime in\b",
    r"\bdate\b",
    r"\btoday\b",
    r"\btomorrow\b",
    r"\byesterday\b",
    r"\badd\b.*\bdays?\b",
    r"\bdifference between\b",
]


def detect_intent(query: str) -> str:
    normalized_query = query.strip().lower()

    if not normalized_query:
        return "unknown"

    if any(
        re.search(pattern, normalized_query)
        for pattern in ALGEBRA_PATTERNS
    ):
        return "algebra"

    if any(
        re.search(pattern, normalized_query)
        for pattern in UNIT_PATTERNS
    ):
        return "unit"

    if any(
        re.search(pattern, normalized_query)
        for pattern in DATETIME_PATTERNS
    ):
        return "datetime"

    return "unknown"