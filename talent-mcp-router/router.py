from typing import Any

import asyncio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError


server = MCPServer("talent-intelligence-mcp")


MCP_SERVERS = {
    "resume": r".\resume-mcp\resume_server.py",
    "job": r".\job-mcp\job_server.py",
    "matching": r".\matching-mcp\matching_server.py",
}


class TalentMCPRouter:
    def __init__(self):
        self.sessions: dict[str, ClientSession] = {}
        self.contexts: dict[str, Any] = {}

    async def connect(self):
        for name, server_file in MCP_SERVERS.items():
            server_params = StdioServerParameters(
                command=r".\.venv\Scripts\python.exe",
                args=[server_file],
            )

            context = stdio_client(server_params)

            read_stream, write_stream = await context.__aenter__()

            client = ClientSession(
                read_stream,
                write_stream,
            )

            await client.__aenter__()
            await client.initialize()

            self.contexts[name] = (context, client)
            self.sessions[name] = client

    async def disconnect(self):
        for context, client in self.contexts.values():
            await client.__aexit__(None, None, None)
            await context.__aexit__(None, None, None)

        self.contexts.clear()
        self.sessions.clear()

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ):
        if tool_name == "inspect_resume":
            session = self.sessions["resume"]

        elif tool_name == "analyze_job":
            session = self.sessions["job"]

        elif tool_name == "compare_skills":
            session = self.sessions["matching"]

        else:
            raise ToolError(
                f"[UNKNOWN_TOOL] Unknown tool: {tool_name}"
            )

        return await session.call_tool(
            tool_name,
            arguments,
        )


router = TalentMCPRouter()


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

    await router.connect()

    try:
        result = await router.call_tool(
            "inspect_resume",
            {
                "resume_text": resume_text.strip(),
            },
        )

        if result.is_error:
            raise ToolError(
                "[RESUME_MCP_ERROR] Resume MCP returned an error."
            )

        return result.structured_content

    finally:
        await router.disconnect()


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

    await router.connect()

    try:
        result = await router.call_tool(
            "analyze_job",
            {
                "job_description": job_description.strip(),
            },
        )

        if result.is_error:
            raise ToolError(
                "[JOB_MCP_ERROR] Job MCP returned an error."
            )

        return result.structured_content

    finally:
        await router.disconnect()


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

    await router.connect()

    try:
        result = await router.call_tool(
            "compare_skills",
            {
                "candidate_skills": candidate_skills,
                "required_skills": required_skills,
            },
        )

        if result.is_error:
            raise ToolError(
                "[MATCHING_MCP_ERROR] Matching MCP returned an error."
            )

        return result.structured_content

    finally:
        await router.disconnect()


if __name__ == "__main__":
    server.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8020,
    )