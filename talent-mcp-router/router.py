from typing import Any

import httpx
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError


server = MCPServer("talent-intelligence-mcp")


MCP_SERVERS = {
    "resume": "http://127.0.0.1:8111/mcp",
    "job": "http://127.0.0.1:8112/mcp",
    "matching": "http://127.0.0.1:8113/mcp",
}


async def call_child_mcp(
    mcp_name: str,
    tool_name: str,
    arguments: dict[str, Any],
):
    if mcp_name not in MCP_SERVERS:
        raise ToolError(
            f"[UNKNOWN_MCP] Unknown MCP server: {mcp_name}"
        )

    server_url = MCP_SERVERS[mcp_name]

    try:
        async with httpx.AsyncClient(timeout=30.0) as http_client:

            async with streamable_http_client(
                server_url,
                http_client=http_client,
            ) as (read_stream, write_stream):

                async with ClientSession(
                    read_stream,
                    write_stream,
                ) as client:

                    await client.initialize()

                    result = await client.call_tool(
                        tool_name,
                        arguments,
                    )

                    if result.is_error:
                        raise ToolError(
                            f"[{mcp_name.upper()}_MCP_ERROR] "
                            f"{tool_name} returned an error."
                        )

                    return result.structured_content

    except ToolError:
        raise

    except httpx.RequestError as exc:
        raise ToolError(
            f"[{mcp_name.upper()}_MCP_UNAVAILABLE] "
            f"Unable to reach {mcp_name} MCP: {exc}"
        )

    except Exception as exc:
        raise ToolError(
            f"[ROUTER_ERROR] Failed to call {mcp_name} MCP: {exc}"
        )


@server.tool()
async def inspect_resume(
    resume_text: str,
) -> dict[str, Any]:
    """
    Inspect a resume through the Resume MCP.
    """

    if not resume_text or not resume_text.strip():
        raise ToolError(
            "[INVALID_INPUT] resume_text cannot be empty"
        )

    return await call_child_mcp(
        "resume",
        "inspect_resume",
        {
            "resume_text": resume_text.strip(),
        },
    )


@server.tool()
async def analyze_job(
    job_description: str,
) -> dict[str, Any]:
    """
    Analyze a job description through the Job MCP.
    """

    if not job_description or not job_description.strip():
        raise ToolError(
            "[INVALID_INPUT] job_description cannot be empty"
        )

    return await call_child_mcp(
        "job",
        "analyze_job",
        {
            "job_description": job_description.strip(),
        },
    )


@server.tool()
async def compare_skills(
    candidate_skills: list[str],
    required_skills: list[str],
) -> dict[str, Any]:
    """
    Compare candidate skills through the Matching MCP.
    """

    if not candidate_skills:
        raise ToolError(
            "[INVALID_INPUT] candidate_skills cannot be empty"
        )

    if not required_skills:
        raise ToolError(
            "[INVALID_INPUT] required_skills cannot be empty"
        )

    return await call_child_mcp(
        "matching",
        "compare_skills",
        {
            "candidate_skills": candidate_skills,
            "required_skills": required_skills,
        },
    )


if __name__ == "__main__":
    server.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8020,
    )