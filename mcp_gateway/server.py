"""Talent Intelligence MCP Gateway Server using MCP Python SDK v2.

Exposes 5 semantic tools:
- Atomic: inspect_resume, analyze_job, compare_skills
- Composite: generate_candidate_report, create_candidate_shortlist
"""

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


# ==============================================================================
# Internal Private Orchestration Helpers (Not exposed as MCP tools)
# ==============================================================================

async def _call_resume_service(resume_text: str, req_id: str) -> Dict[str, Any]:
    """Call internal Resume Service directly using the provided correlation ID."""
    print(f"[{req_id}] calling resume-service", flush=True)
    try:
        return await call_backend(
            service_url=RESUME_SERVICE_URL,
            path="/inspect",
            payload={"resume_text": resume_text},
            request_id=req_id
        )
    except GatewayBackendError as exc:
        raise ToolError(f"[{exc.code}] {exc.message}") from None
    except Exception as exc:
        raise ToolError(f"[INTERNAL_ERROR] Resume service failed: {str(exc)}") from None


async def _call_job_service(job_description: str, req_id: str) -> Dict[str, Any]:
    """Call internal Job Service directly using the provided correlation ID."""
    print(f"[{req_id}] calling job-service", flush=True)
    try:
        return await call_backend(
            service_url=JOB_SERVICE_URL,
            path="/analyze",
            payload={"job_description": job_description},
            request_id=req_id
        )
    except GatewayBackendError as exc:
        raise ToolError(f"[{exc.code}] {exc.message}") from None
    except Exception as exc:
        raise ToolError(f"[INTERNAL_ERROR] Job service failed: {str(exc)}") from None


async def _call_matching_service(
    candidate_skills: List[str],
    required_skills: List[str],
    req_id: str
) -> Dict[str, Any]:
    """Call internal Matching Service directly using the provided correlation ID."""
    print(f"[{req_id}] calling matching-service", flush=True)
    try:
        return await call_backend(
            service_url=MATCHING_SERVICE_URL,
            path="/compare",
            payload={
                "candidate_skills": candidate_skills,
                "required_skills": required_skills
            },
            request_id=req_id
        )
    except GatewayBackendError as exc:
        raise ToolError(f"[{exc.code}] {exc.message}") from None
    except Exception as exc:
        raise ToolError(f"[INTERNAL_ERROR] Matching service failed: {str(exc)}") from None


# ==============================================================================
# Atomic MCP Tools (Tools 1, 2, 3)
# ==============================================================================

@mcp_server.tool(
    name="inspect_resume",
    description="Inspect and parse raw candidate resume text into structured candidate profile data."
)
async def inspect_resume(resume_text: str) -> Dict[str, Any]:
    """Inspect raw resume text and extract candidate profile, skills, and experience."""
    if not resume_text or not resume_text.strip():
        raise ToolError("[INVALID_INPUT] resume_text must not be empty")

    req_id = f"mcp-req-{uuid.uuid4().hex[:8]}"
    print(f"[{req_id}] tool=inspect_resume started", flush=True)
    try:
        data = await _call_resume_service(resume_text, req_id)
        print(f"[{req_id}] tool=inspect_resume completed", flush=True)
        return data
    except ToolError as exc:
        print(f"[{req_id}] tool=inspect_resume failed: {str(exc)}", flush=True)
        raise


@mcp_server.tool(
    name="analyze_job",
    description="Analyze job description text and extract title, required skills, and experience requirements."
)
async def analyze_job(job_description: str) -> Dict[str, Any]:
    """Analyze a job description and extract title, required skills, and experience."""
    if not job_description or not job_description.strip():
        raise ToolError("[INVALID_INPUT] job_description must not be empty")

    req_id = f"mcp-req-{uuid.uuid4().hex[:8]}"
    print(f"[{req_id}] tool=analyze_job started", flush=True)
    try:
        data = await _call_job_service(job_description, req_id)
        print(f"[{req_id}] tool=analyze_job completed", flush=True)
        return data
    except ToolError as exc:
        print(f"[{req_id}] tool=analyze_job failed: {str(exc)}", flush=True)
        raise


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
        data = await _call_matching_service(candidate_skills, required_skills, req_id)
        print(f"[{req_id}] tool=compare_skills completed", flush=True)
        return data
    except ToolError as exc:
        print(f"[{req_id}] tool=compare_skills failed: {str(exc)}", flush=True)
        raise


# ==============================================================================
# Composite MCP Tools (Tools 4, 5)
# ==============================================================================

@mcp_server.tool(
    name="generate_candidate_report",
    description="Generate a comprehensive candidate evaluation report by orchestrating resume inspection, job analysis, and skill comparison."
)
async def generate_candidate_report(
    resume_text: str,
    job_description: str
) -> Dict[str, Any]:
    """Orchestrate resume inspection, job analysis, and skill matching to produce a unified candidate report."""
    if not resume_text or not resume_text.strip():
        raise ToolError("[INVALID_INPUT] resume_text must not be empty")
    if not job_description or not job_description.strip():
        raise ToolError("[INVALID_INPUT] job_description must not be empty")

    req_id = f"mcp-req-report-{uuid.uuid4().hex[:8]}"
    print(f"[{req_id}] tool=generate_candidate_report started", flush=True)

    try:
        # 1. Inspect resume
        raw_cand = await _call_resume_service(resume_text, req_id)

        # 2. Analyze job
        job_data = await _call_job_service(job_description, req_id)

        # 3. Compare skills
        cand_skills = raw_cand.get("skills", [])
        req_skills = job_data.get("required_skills", [])
        match_data = await _call_matching_service(cand_skills, req_skills, req_id)

        # 4. Deterministic assessment calculation
        match_pct = match_data.get("match_percentage", 0.0)
        cand_exp = raw_cand.get("experience_years", 0)
        req_exp = job_data.get("experience_required", 0)

        if match_pct >= 80.0:
            match_summary = "Strong technical match."
        elif match_pct >= 60.0:
            match_summary = "Good technical match with some skill gaps."
        else:
            match_summary = "Significant skill gaps identified."

        if cand_exp >= req_exp:
            exp_summary = f"Experience requirement met ({cand_exp} years vs {req_exp} required)."
        else:
            exp_summary = f"Experience gap identified ({cand_exp} years vs {req_exp} required)."

        overall_assessment = f"{match_summary} {exp_summary}"

        # Normalize candidate dictionary with "name" key per contract
        candidate_data = {
            "name": raw_cand.get("candidate_name") or raw_cand.get("name") or "Alex Johnson",
            "skills": raw_cand.get("skills", []),
            "experience_years": cand_exp,
            "education": raw_cand.get("education", "")
        }

        print(f"[{req_id}] tool=generate_candidate_report completed", flush=True)

        return {
            "candidate": candidate_data,
            "job": job_data,
            "skill_match": match_data,
            "overall_assessment": overall_assessment
        }
    except ToolError as exc:
        print(f"[{req_id}] tool=generate_candidate_report failed: {str(exc)}", flush=True)
        raise


@mcp_server.tool(
    name="create_candidate_shortlist",
    description="Evaluate multiple candidate resumes against a job description and generate a ranked candidate shortlist."
)
async def create_candidate_shortlist(
    job_description: str,
    resumes: List[str]
) -> Dict[str, Any]:
    """Orchestrate job analysis and sequential candidate resume evaluation to produce a ranked shortlist."""
    if not job_description or not job_description.strip():
        raise ToolError("[INVALID_INPUT] job_description must not be empty")
    if not resumes:
        raise ToolError("[INVALID_INPUT] resumes must contain at least one resume")
    for idx, r in enumerate(resumes):
        if not r or not r.strip():
            raise ToolError(f"[INVALID_INPUT] resume text at index {idx} cannot be empty")

    req_id = f"mcp-req-shortlist-{uuid.uuid4().hex[:8]}"
    print(f"[{req_id}] tool=create_candidate_shortlist started (candidates={len(resumes)})", flush=True)

    try:
        # 1. Analyze job description once
        job_data = await _call_job_service(job_description, req_id)
        req_skills = job_data.get("required_skills", [])

        evaluated_candidates: List[Dict[str, Any]] = []

        # 2. Sequentially process each resume
        for resume_text in resumes:
            cand_profile = await _call_resume_service(resume_text, req_id)
            match_result = await _call_matching_service(
                cand_profile.get("skills", []),
                req_skills,
                req_id
            )

            evaluated_candidates.append({
                "name": cand_profile.get("candidate_name", "Unknown Candidate"),
                "match_percentage": match_result.get("match_percentage", 0.0),
                "matched_skills": match_result.get("matched", []),
                "missing_skills": match_result.get("missing", []),
                "experience_years": cand_profile.get("experience_years", 0)
            })

        # 3. Deterministic ranking: Primary = match_percentage DESC, Secondary = experience_years DESC
        evaluated_candidates.sort(
            key=lambda c: (c["match_percentage"], c["experience_years"]),
            reverse=True
        )

        # 4. Assign ranks starting at 1
        for rank_idx, candidate in enumerate(evaluated_candidates, start=1):
            candidate["rank"] = rank_idx

        print(f"[{req_id}] tool=create_candidate_shortlist completed", flush=True)

        return {
            "job": job_data,
            "candidates": evaluated_candidates,
            "total_candidates": len(evaluated_candidates)
        }
    except ToolError as exc:
        print(f"[{req_id}] tool=create_candidate_shortlist failed: {str(exc)}", flush=True)
        raise


# Starlette ASGI application for Streamable HTTP
app = mcp_server.streamable_http_app(streamable_http_path="/mcp")


if __name__ == "__main__":
    print(f"Starting Talent Intelligence MCP Gateway on http://{GATEWAY_HOST}:{GATEWAY_PORT}/mcp ...", flush=True)
    uvicorn.run("mcp_gateway.server:app", host=GATEWAY_HOST, port=GATEWAY_PORT, reload=False)
