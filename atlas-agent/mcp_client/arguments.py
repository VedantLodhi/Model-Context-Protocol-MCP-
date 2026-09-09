import re


class ToolArgumentBuilder:
    """
    Converts natural-language user queries into
    arguments expected by MCP tools.

    This class does NOT:
    - connect to MCP servers
    - detect intent
    - invoke tools

    It only prepares tool arguments.
    """

    @staticmethod
    def algebra(query: str) -> dict:
        problem = query.strip()

        prefixes = (
            "solve ",
            "calculate ",
            "find x for ",
            "find x in ",
        )

        normalized = problem.lower()

        for prefix in prefixes:
            if normalized.startswith(prefix):
                problem = problem[len(prefix):].strip()
                break

        return {
            "problem": problem,
        }

    @staticmethod
    def unit(query: str) -> dict:
        pattern = (
            r"(-?\d+(?:\.\d+)?)\s*"
            r"([a-zA-Z°]+)\s+"
            r"(?:to|into|in)\s+"
            r"([a-zA-Z°]+)"
        )

        match = re.search(pattern, query)

        if not match:
            raise ValueError(
                "Could not understand the unit conversion."
            )

        return {
            "value": float(match.group(1)),
            "from_unit": match.group(2),
            "to_unit": match.group(3),
        }

    @staticmethod
    def datetime(query: str) -> dict:
        timezone = ToolArgumentBuilder._detect_timezone(query)

        return {
            "operation": "now",
            "timezone": timezone,
        }

    @staticmethod
    def _detect_timezone(query: str) -> str:
        normalized = query.lower()

        timezone_map = {
            "india": "Asia/Kolkata",
            "london": "Europe/London",
            "new york": "America/New_York",
            "tokyo": "Asia/Tokyo",
        }

        for location, timezone in timezone_map.items():
            if location in normalized:
                return timezone

        return "UTC"