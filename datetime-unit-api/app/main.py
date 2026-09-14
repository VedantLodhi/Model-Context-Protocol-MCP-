from datetime import datetime, timedelta
from typing import Any

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pint
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


app = FastAPI(
    title="DateTime Unit API",
    version="1.0.0",
    description="Backend API for date/time and unit operations.",
)


ureg = pint.UnitRegistry()


class UnitConversionRequest(BaseModel):
    value: float
    from_unit: str = Field(min_length=1)
    to_unit: str = Field(min_length=1)


class DateTimeRequest(BaseModel):
    operation: str = Field(min_length=1)
    date: str | None = None
    end_date: str | None = None
    days: int = 0
    timezone: str = "UTC"


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "datetime-unit-api",
    }


@app.post("/convert")
async def convert_units(
    request: UnitConversionRequest,
) -> dict[str, Any]:

    from_unit = request.from_unit.strip()
    to_unit = request.to_unit.strip()

    if not from_unit:
        raise HTTPException(
            status_code=400,
            detail="[INVALID_INPUT] from_unit cannot be empty",
        )

    if not to_unit:
        raise HTTPException(
            status_code=400,
            detail="[INVALID_INPUT] to_unit cannot be empty",
        )

    try:
        source = ureg.Quantity(
            request.value,
            from_unit,
        )

        converted = source.to(to_unit)

        return {
            "value": request.value,
            "from_unit": from_unit,
            "to_unit": to_unit,
            "result": float(converted.magnitude),
            "result_unit": str(converted.units),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                "[INVALID_INPUT] "
                f"Unable to convert units: {exc}"
            ),
        )


@app.post("/datetime")
async def date_time(
    request: DateTimeRequest,
) -> dict[str, Any]:

    operation = request.operation.strip().lower()

    if not operation:
        raise HTTPException(
            status_code=400,
            detail="[INVALID_INPUT] operation cannot be empty",
        )

    try:

        if operation == "now":
            try:
                current_time = datetime.now(
                    ZoneInfo(request.timezone)
                )
            except ZoneInfoNotFoundError:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "[INVALID_INPUT] "
                        f"Unknown timezone: {request.timezone}"
                    ),
                )

            return {
                "operation": "now",
                "timezone": request.timezone,
                "datetime": current_time.isoformat(),
            }

        if operation == "add_days":

            if not request.date:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "[INVALID_INPUT] "
                        "date is required for add_days"
                    ),
                )

            parsed_date = datetime.fromisoformat(
                request.date
            )

            result_date = (
                parsed_date
                + timedelta(days=request.days)
            )

            return {
                "operation": "add_days",
                "input_date": request.date,
                "days": request.days,
                "result": result_date.isoformat(),
            }

        if operation == "difference":

            if not request.date or not request.end_date:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "[INVALID_INPUT] "
                        "date and end_date are required "
                        "for difference"
                    ),
                )

            first_date = datetime.fromisoformat(
                request.date
            )

            second_date = datetime.fromisoformat(
                request.end_date
            )

            difference = second_date - first_date

            return {
                "operation": "difference",
                "first_date": request.date,
                "second_date": request.end_date,
                "difference_days": difference.days,
                "difference_seconds": difference.total_seconds(),
            }

        raise HTTPException(
            status_code=400,
            detail=(
                "[INVALID_INPUT] "
                f"Unsupported operation: {operation}"
            ),
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                "[INVALID_INPUT] "
                f"Unable to process date/time: {exc}"
            ),
        )