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
    ToolCapability(
        server="algebra",
        tool_name="solve_algebra",
        intent="algebra",
        description=(
            "Solve algebraic equations and simplify "
            "algebraic expressions."
        ),
    ),
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
]


def get_capabilities() -> list[ToolCapability]:
    """
    Return all capabilities available to Atlas.
    """

    return list(CAPABILITIES)