from typing import Any

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError


server = MCPServer("matching-mcp")

MATCHING_API_URL = "http://127.0.0.1:8003"


async def _call_matching_api(
    endpoint: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{MATCHING_API_URL}{endpoint}",
                json=payload,
            )

        if response.status_code >= 400:
            try:
                error_data = response.json()
                detail = error_data.get(
                    "detail",
                    "Matching API request failed.",
                )
            except Exception:
                detail = response.text

            raise ToolError(str(detail))

        return response.json()

    except ToolError:
        raise

    except httpx.RequestError as exc:
        raise ToolError(
            "[BACKEND_UNAVAILABLE] Unable to reach Matching API: "
            f"{exc}"
        )

    except Exception as exc:
        raise ToolError(
            "[MCP_ERROR] Unable to execute Matching MCP tool: "
            f"{exc}"
        )


@server.tool()
async def compare_skills(
    candidate_skills: list[str],
    required_skills: list[str],
) -> dict[str, Any]:
    """
    Compare candidate skills against required job skills.

    The actual skill matching is performed by the Matching API.
    """

    if not candidate_skills:
        raise ToolError(
            "[INVALID_INPUT] candidate_skills cannot be empty"
        )

    if not required_skills:
        raise ToolError(
            "[INVALID_INPUT] required_skills cannot be empty"
        )

    return await _call_matching_api(
        "/compare",
        {
            "candidate_skills": candidate_skills,
            "required_skills": required_skills,
        },
    )


if __name__ == "__main__":
    server.run()