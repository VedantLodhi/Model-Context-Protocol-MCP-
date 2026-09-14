from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from sympy import solve
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
)


app = FastAPI(
    title="Algebra API",
    version="1.0.0",
    description="Backend API for algebra calculations.",
)


TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
)


class SolveRequest(BaseModel):
    problem: str = Field(min_length=1)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "algebra-api",
    }


@app.post("/solve")
async def solve_algebra(
    request: SolveRequest,
) -> dict[str, Any]:

    problem = request.problem.strip()

    if not problem:
        raise HTTPException(
            status_code=400,
            detail="[INVALID_INPUT] problem cannot be empty",
        )

    problem = problem.replace("^", "**")

    try:
        if "=" in problem:
            left, right = problem.split("=", 1)

            left_expr = parse_expr(
                left,
                transformations=TRANSFORMATIONS,
            )

            right_expr = parse_expr(
                right,
                transformations=TRANSFORMATIONS,
            )

            equation = left_expr - right_expr

            symbols = sorted(
                equation.free_symbols,
                key=lambda symbol: str(symbol),
            )

            if not symbols:
                result = "True" if equation == 0 else "False"

                return {
                    "problem": problem,
                    "solution": result,
                    "steps": [
                        f"Evaluate: {left} = {right}",
                        f"Result: {result}",
                    ],
                }

            solutions = solve(
                equation,
                symbols,
            )

            return {
                "problem": problem,
                "solution": [
                    str(value)
                    for value in solutions
                ],
                "steps": [
                    f"Equation: {problem}",
                    f"Variable(s): {', '.join(str(s) for s in symbols)}",
                    (
                        "Solution: "
                        + ", ".join(
                            str(value)
                            for value in solutions
                        )
                    ),
                ],
            }

        expression = parse_expr(
            problem,
            transformations=TRANSFORMATIONS,
        )

        simplified = expression.simplify()

        return {
            "problem": problem,
            "solution": str(simplified),
            "steps": [
                f"Expression: {problem}",
                f"Simplified result: {simplified}",
            ],
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                "[INVALID_INPUT] "
                f"Unable to solve algebra problem: {exc}"
            ),
        )