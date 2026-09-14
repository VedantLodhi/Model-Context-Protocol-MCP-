from dataclasses import dataclass


@dataclass(frozen=True)
class ToolCapability:
    """
    Describes what an MCP tool is capable of doing.
    """

    server: str
    tool_name: str
    intent: str
    description: str


CAPABILITIES = [
    # ---------------------------------------------------------
    # Algebra MCP
    # ---------------------------------------------------------

    ToolCapability(
        server="algebra",
        tool_name="solve_algebra",
        intent="algebra",
        description=(
            "Solve algebraic equations and simplify "
            "algebraic expressions."
        ),
    ),

    # ---------------------------------------------------------
    # DateTime / Unit MCP
    # ---------------------------------------------------------

    ToolCapability(
        server="datetime_unit",
        tool_name="convert_units",
        intent="unit",
        description=(
            "Convert a numeric value from one unit "
            "to another unit."
        ),
    ),

    ToolCapability(
        server="datetime_unit",
        tool_name="date_time",
        intent="datetime",
        description=(
            "Get the current time for a requested "
            "timezone."
        ),
    ),

    # ---------------------------------------------------------
    # Talent Intelligence MCP
    # ---------------------------------------------------------

    ToolCapability(
        server="talent",
        tool_name="inspect_resume",
        intent="talent_resume",
        description=(
            "Inspect a resume and extract structured "
            "candidate information."
        ),
    ),

    ToolCapability(
        server="talent",
        tool_name="analyze_job",
        intent="talent_job",
        description=(
            "Analyze a job description and extract "
            "structured job requirements."
        ),
    ),

    ToolCapability(
        server="talent",
        tool_name="compare_skills",
        intent="talent_matching",
        description=(
            "Compare candidate skills against "
            "required job skills."
        ),
    ),
]


def get_capabilities() -> list[ToolCapability]:
    """
    Return all capabilities available to Atlas.
    """

    return list(CAPABILITIES)