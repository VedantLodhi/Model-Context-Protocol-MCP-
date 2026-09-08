"""Talent Intelligence MCP Gateway Server using MCP Python SDK v2."""

import logging
import uuid
from typing import Any, Dict, List
import uvicorn
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp_gateway.client import GatewayBackendError, call_backend
from mcp_gateway.config import (
    GATEWAY_HOST,
    GATEWAY_PORT,
    JOB_SERVICE_URL,
    MATCHING_SERVICE_URL,
    RESUME_SERVICE_URL,
)

logger = logging.getLogger("mcp_gateway")

# Initialize MCP Server v2
mcp_server = MCPServer("Talent Intelligence MCP Gateway")


@mcp_server.tool(
    name="inspect_resume",
    description="Inspect and parse raw candidate resume text into structured candidate profile data."
)
async def inspect_resume(resume_text: str) -> Dict[str, Any]:
    """Inspect raw resume text and extract candidate profile, skills, and experience."""
    req_id = f"mcp-req-{uuid.uuid4().hex[:8]}"
    print(f"[{req_id}] tool=inspect_resume started", flush=True)

    try:
        print(f"[{req_id}] calling resume-service", flush=True)
        data = await call_backend(
            service_url=RESUME_SERVICE_URL,
            path="/inspect",
            payload={"resume_text": resume_text},
            request_id=req_id
        )
        print(f"[{req_id}] tool=inspect_resume completed", flush=True)
        return data
    except GatewayBackendError as exc:
        print(f"[{req_id}] tool=inspect_resume failed: [{exc.code}] {exc.message}", flush=True)
        raise ToolError(f"[{exc.code}] {exc.message}") from None
    except Exception as exc:
        print(f"[{req_id}] tool=inspect_resume unexpected error: {str(exc)}", flush=True)
        raise ToolError(f"[INTERNAL_ERROR] An unexpected error occurred: {str(exc)}") from None


@mcp_server.tool(
    name="analyze_job",
    description="Analyze job description text and extract title, required skills, and experience requirements."
)
async def analyze_job(job_description: str) -> Dict[str, Any]:
    """Analyze a job description and extract title, required skills, and experience."""
    req_id = f"mcp-req-{uuid.uuid4().hex[:8]}"
    print(f"[{req_id}] tool=analyze_job started", flush=True)

    try:
        print(f"[{req_id}] calling job-service", flush=True)
        data = await call_backend(
            service_url=JOB_SERVICE_URL,
            path="/analyze",
            payload={"job_description": job_description},
            request_id=req_id
        )
        print(f"[{req_id}] tool=analyze_job completed", flush=True)
        return data
    except GatewayBackendError as exc:
        print(f"[{req_id}] tool=analyze_job failed: [{exc.code}] {exc.message}", flush=True)
        raise ToolError(f"[{exc.code}] {exc.message}") from None
    except Exception as exc:
        print(f"[{req_id}] tool=analyze_job unexpected error: {str(exc)}", flush=True)
        raise ToolError(f"[INTERNAL_ERROR] An unexpected error occurred: {str(exc)}") from None


@mcp_server.tool(
    name="compare_skills",
    description="Compare candidate skills against job required skills and calculate match percentage."
)
async def compare_skills(
    candidate_skills: List[str],
    required_skills: List[str]
) -> Dict[str, Any]:
    """Compare candidate skills against required skills and return matched, missing, and match percentage."""
    req_id = f"mcp-req-{uuid.uuid4().hex[:8]}"
    print(f"[{req_id}] tool=compare_skills started", flush=True)

    try:
        print(f"[{req_id}] calling matching-service", flush=True)
        data = await call_backend(
            service_url=MATCHING_SERVICE_URL,
            path="/compare",
            payload={
                "candidate_skills": candidate_skills,
                "required_skills": required_skills
            },
            request_id=req_id
        )
        print(f"[{req_id}] tool=compare_skills completed", flush=True)
        return data
    except GatewayBackendError as exc:
        print(f"[{req_id}] tool=compare_skills failed: [{exc.code}] {exc.message}", flush=True)
        raise ToolError(f"[{exc.code}] {exc.message}") from None
    except Exception as exc:
        print(f"[{req_id}] tool=compare_skills unexpected error: {str(exc)}", flush=True)
        raise ToolError(f"[INTERNAL_ERROR] An unexpected error occurred: {str(exc)}") from None


# Starlette ASGI application for Streamable HTTP
app = mcp_server.streamable_http_app(streamable_http_path="/mcp")


if __name__ == "__main__":
    print(f"Starting Talent Intelligence MCP Gateway on http://{GATEWAY_HOST}:{GATEWAY_PORT}/mcp ...", flush=True)
    uvicorn.run("mcp_gateway.server:app", host=GATEWAY_HOST, port=GATEWAY_PORT, reload=False)
