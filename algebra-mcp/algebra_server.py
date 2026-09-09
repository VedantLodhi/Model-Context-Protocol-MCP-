from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from sympy import solve
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
)


server = MCPServer("algebra-mcp")


TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
)


@server.tool()
async def solve_algebra(problem: str) -> dict[str, Any]:
    """
    Solve a mathematical or algebraic problem.

    Examples:
    - 2x + 5 = 15
    - x^2 - 5x + 6 = 0
    - 2(x + 3) = 14
    """

    if not problem or not problem.strip():
        raise ToolError("[INVALID_INPUT] problem cannot be empty")

    problem = problem.strip()
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

            solutions = solve(equation, symbols)

            return {
                "problem": problem,
                "solution": [str(value) for value in solutions],
                "steps": [
                    f"Equation: {problem}",
                    f"Variable(s): {', '.join(str(s) for s in symbols)}",
                    f"Solution: {', '.join(str(value) for value in solutions)}",
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
        raise ToolError(
            f"[INVALID_INPUT] Unable to solve algebra problem: {exc}"
        )


if __name__ == "__main__":
    server.run()