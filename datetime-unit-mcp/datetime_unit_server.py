from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import pint

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError


server = MCPServer("datetime-unit-mcp")

# Unit conversion engine
ureg = pint.UnitRegistry()


@server.tool()
async def convert_units(
    value: float,
    from_unit: str,
    to_unit: str,
) -> dict[str, Any]:

    if not from_unit or not from_unit.strip():
        raise ToolError("[INVALID_INPUT] from_unit cannot be empty")

    if not to_unit or not to_unit.strip():
        raise ToolError("[INVALID_INPUT] to_unit cannot be empty")

    try:
        source = ureg.Quantity(value, from_unit.strip())
        converted = source.to(to_unit.strip())

        return {
            "value": value,
            "from_unit": from_unit.strip(),
            "to_unit": to_unit.strip(),
            "result": float(converted.magnitude),
            "result_unit": str(converted.units),
        }

    except Exception as exc:
        raise ToolError(
            f"[INVALID_INPUT] Unable to convert units: {exc}"
        )


@server.tool()
async def date_time(
    operation: str,
    date: str | None = None,
    days: int = 0,
    timezone: str = "UTC",
) -> dict[str, Any]:

    if not operation or not operation.strip():
        raise ToolError("[INVALID_INPUT] operation cannot be empty")

    operation = operation.strip().lower()

    try:
        if operation == "now":
            current_time = datetime.now(ZoneInfo(timezone))

            return {
                "operation": "now",
                "timezone": timezone,
                "datetime": current_time.isoformat(),
            }

        if operation == "add_days":
            if not date:
                raise ToolError(
                    "[INVALID_INPUT] date is required for add_days"
                )

            parsed_date = datetime.fromisoformat(date)
            result_date = parsed_date + timedelta(days=days)

            return {
                "operation": "add_days",
                "input_date": date,
                "days": days,
                "result": result_date.isoformat(),
            }

        if operation == "difference":
            if not date:
                raise ToolError(
                    "[INVALID_INPUT] date is required for difference"
                )

            parts = date.split(",")

            if len(parts) != 2:
                raise ToolError(
                    "[INVALID_INPUT] difference requires two dates "
                    "separated by a comma"
                )

            first_date = datetime.fromisoformat(parts[0].strip())
            second_date = datetime.fromisoformat(parts[1].strip())

            difference = second_date - first_date

            return {
                "operation": "difference",
                "first_date": parts[0].strip(),
                "second_date": parts[1].strip(),
                "difference_days": difference.days,
                "difference_seconds": difference.total_seconds(),
            }

        raise ToolError(
            f"[INVALID_INPUT] Unsupported operation: {operation}"
        )

    except ToolError:
        raise

    except Exception as exc:
        raise ToolError(
            f"[INVALID_INPUT] Unable to process date/time: {exc}"
        )


if __name__ == "__main__":
    server.run()