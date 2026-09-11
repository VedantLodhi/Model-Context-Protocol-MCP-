from typing import Any

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError


server = MCPServer("resume-mcp")

RESUME_API_URL = "http://127.0.0.1:8001"


async def _call_resume_api(
    endpoint: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{RESUME_API_URL}{endpoint}",
                json=payload,
            )

        if response.status_code >= 400:
            try:
                error_data = response.json()
                detail = error_data.get(
                    "detail",
                    "Resume API request failed.",
                )
            except Exception:
                detail = response.text

            raise ToolError(str(detail))

        return response.json()

    except ToolError:
        raise

    except httpx.RequestError as exc:
        raise ToolError(
            "[BACKEND_UNAVAILABLE] Unable to reach Resume API: "
            f"{exc}"
        )

    except Exception as exc:
        raise ToolError(
            "[MCP_ERROR] Unable to execute Resume MCP tool: "
            f"{exc}"
        )


@server.tool()
async def inspect_resume(resume_text: str) -> dict[str, Any]:
    """
    Inspect a resume and extract structured candidate information.

    The actual resume processing is performed by the Resume API.
    """

    if not resume_text or not resume_text.strip():
        raise ToolError(
            "[INVALID_INPUT] resume_text cannot be empty"
        )

    return await _call_resume_api(
        "/inspect",
        {
            "resume_text": resume_text.strip(),
        },
    )


if __name__ == "__main__":
    server.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8111,
    )