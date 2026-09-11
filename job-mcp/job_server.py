from typing import Any

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError


server = MCPServer("job-mcp")

JOB_API_URL = "http://127.0.0.1:8002"


async def _call_job_api(
    endpoint: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{JOB_API_URL}{endpoint}",
                json=payload,
            )

        if response.status_code >= 400:
            try:
                error_data = response.json()
                detail = error_data.get(
                    "detail",
                    "Job API request failed.",
                )
            except Exception:
                detail = response.text

            raise ToolError(str(detail))

        return response.json()

    except ToolError:
        raise

    except httpx.RequestError as exc:
        raise ToolError(
            "[BACKEND_UNAVAILABLE] Unable to reach Job API: "
            f"{exc}"
        )

    except Exception as exc:
        raise ToolError(
            "[MCP_ERROR] Unable to execute Job MCP tool: "
            f"{exc}"
        )


@server.tool()
async def analyze_job(job_description: str) -> dict[str, Any]:
    """
    Analyze a job description and extract structured requirements.

    The actual job analysis is performed by the Job API.
    """

    if not job_description or not job_description.strip():
        raise ToolError(
            "[INVALID_INPUT] job_description cannot be empty"
        )

    return await _call_job_api(
        "/analyze",
        {
            "job_description": job_description.strip(),
        },
    )


if __name__ == "__main__":
    server.run()