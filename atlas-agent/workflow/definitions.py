import re


UNIT_CHAIN_PATTERN = re.compile(
    r"""
    convert\s+
    (-?\d+(?:\.\d+)?)\s+
    ([a-zA-Z°]+)
    \s+to\s+
    ([a-zA-Z°]+)
    .*?
    convert\s+
    (?:that\s+result|the\s+result)
    \s+to\s+
    ([a-zA-Z°]+)
    """,
    re.IGNORECASE | re.VERBOSE,
)


TALENT_EVALUATION_PATTERN = re.compile(
    r"""
    evaluate\s+candidate
    \s*
    resume\s*:\s*
    (?P<resume>.*?)
    \s*
    job\s*:\s*
    (?P<job>.*)
    """,
    re.IGNORECASE | re.DOTALL | re.VERBOSE,
)


def parse_unit_conversion_chain(
    query: str,
) -> dict | None:

    match = UNIT_CHAIN_PATTERN.search(query)

    if not match:
        return None

    return {
        "value": float(match.group(1)),
        "from_unit": match.group(2),
        "intermediate_unit": match.group(3),
        "to_unit": match.group(4),
    }


def parse_talent_evaluation(
    query: str,
) -> dict | None:

    match = TALENT_EVALUATION_PATTERN.search(query)

    if not match:
        return None

    resume = match.group("resume").strip()
    job = match.group("job").strip()

    if not resume or not job:
        return None

    return {
        "resume_text": resume,
        "job_description": job,
    }


def is_workflow_query(query: str) -> bool:
    return (
        parse_unit_conversion_chain(query)
        is not None
    )


def is_talent_evaluation_query(query: str) -> bool:
    return (
        parse_talent_evaluation(query)
        is not None
    )