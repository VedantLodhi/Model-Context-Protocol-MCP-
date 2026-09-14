from typing import Any

import httpx

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError


server = MCPServer("algebra-mcp")

API_URL = "http://127.0.0.1:8011"


@server.tool()
async def solve_algebra(problem: str) -> dict[str, Any]:
    if not problem or not problem.strip():
        raise ToolError(
            "[INVALID_INPUT] problem cannot be empty"
        )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{API_URL}/solve",
                json={
                    "problem": problem.strip(),
                },
            )

        if response.status_code >= 400:
            try:
                error_data = response.json()
                detail = error_data.get(
                    "detail",
                    "Algebra API request failed.",
                )
            except Exception:
                detail = response.text

            raise ToolError(str(detail))

        return response.json()

    except ToolError:
        raise

    except httpx.RequestError as exc:
        raise ToolError(
            "[BACKEND_UNAVAILABLE] "
            f"Unable to reach Algebra API: {exc}"
        )

    except Exception as exc:
        raise ToolError(
            "[MCP_ERROR] "
            f"Unable to execute algebra tool: {exc}"
        )


if __name__ == "__main__":
    server.run()