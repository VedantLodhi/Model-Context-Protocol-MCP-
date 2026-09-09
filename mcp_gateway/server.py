"""
Talent Intelligence MCP Gateway Server.

Exposes six semantic MCP tools:
1. inspect_resume
2. analyze_job
3. compare_skills
4. generate_candidate_report
5. create_candidate_shortlist
6. get_github_profile

The gateway handles:
- MCP protocol
- authentication
- authorization
- correlation/request IDs
- backend routing
- composite capability orchestration
- GitHub integration

Business logic remains inside backend services.
"""

from typing import Any

from mcp.server.mcpserver import Context, MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from mcp_gateway.client import GatewayBackendError, call_backend
from mcp_gateway.config import (
    JOB_SERVICE_URL,
    MATCHING_SERVICE_URL,
    RESUME_SERVICE_URL,
)
from mcp_gateway.github_client import (
    GitHubClientError,
    get_user,
    get_user_repositories,
)
from mcp_gateway.security import authorize


server = MCPServer("talent-intelligence-gateway")


def _get_api_key(ctx: Context) -> str | None:
    """Read the demo API key from the incoming HTTP headers."""
    headers = ctx.headers or {}
    return headers.get("x-api-key") or headers.get("X-API-Key")


def _get_request_id(ctx: Context) -> str:
    """Use MCP request ID as correlation ID when available."""
    request_id = getattr(ctx, "request_id", None)

    if request_id:
        return str(request_id)

    return "mcp-request"


def _handle_backend_error(exc: GatewayBackendError) -> None:
    """Convert backend errors into MCP ToolError responses."""
    raise ToolError(f"[{exc.code}] {exc.message}")


async def _call_resume_service(
    payload: dict[str, Any],
    request_id: str,
) -> dict[str, Any]:
    try:
        return await call_backend(
            RESUME_SERVICE_URL,
            "/inspect",
            payload,
            request_id,
        )
    except GatewayBackendError as exc:
        _handle_backend_error(exc)

    raise RuntimeError("Unreachable")


async def _call_job_service(
    payload: dict[str, Any],
    request_id: str,
) -> dict[str, Any]:
    try:
        return await call_backend(
            JOB_SERVICE_URL,
            "/analyze",
            payload,
            request_id,
        )
    except GatewayBackendError as exc:
        _handle_backend_error(exc)

    raise RuntimeError("Unreachable")


async def _call_matching_service(
    payload: dict[str, Any],
    request_id: str,
) -> dict[str, Any]:
    try:
        return await call_backend(
            MATCHING_SERVICE_URL,
            "/compare",
            payload,
            request_id,
        )
    except GatewayBackendError as exc:
        _handle_backend_error(exc)

    raise RuntimeError("Unreachable")


@server.tool()
async def inspect_resume(
    resume_text: str,
    ctx: Context,
) -> dict[str, Any]:
    """
    Inspect a resume and extract structured candidate information.

    Returns:
    - candidate name
    - email
    - phone
    - skills
    - experience years
    - education
    - raw text length
    """

    api_key = _get_api_key(ctx)
    authorize(api_key, "inspect_resume")

    if not resume_text or not resume_text.strip():
        raise ToolError(
            "[INVALID_INPUT] resume_text cannot be empty"
        )

    request_id = _get_request_id(ctx)

    return await _call_resume_service(
        {
            "resume_text": resume_text,
        },
        request_id,
    )


@server.tool()
async def analyze_job(
    job_description: str,
    ctx: Context,
) -> dict[str, Any]:
    """
    Analyze a job description and extract structured requirements.
    """

    api_key = _get_api_key(ctx)
    authorize(api_key, "analyze_job")

    if not job_description or not job_description.strip():
        raise ToolError(
            "[INVALID_INPUT] job_description cannot be empty"
        )

    request_id = _get_request_id(ctx)

    return await _call_job_service(
        {
            "job_description": job_description,
        },
        request_id,
    )


@server.tool()
async def compare_skills(
    candidate_skills: list[str],
    required_skills: list[str],
    ctx: Context,
) -> dict[str, Any]:
    """
    Compare candidate skills against required job skills.
    """

    api_key = _get_api_key(ctx)
    authorize(api_key, "compare_skills")

    if not candidate_skills:
        raise ToolError(
            "[INVALID_INPUT] candidate_skills cannot be empty"
        )

    if not required_skills:
        raise ToolError(
            "[INVALID_INPUT] required_skills cannot be empty"
        )

    request_id = _get_request_id(ctx)

    return await _call_matching_service(
        {
            "candidate_skills": candidate_skills,
            "required_skills": required_skills,
        },
        request_id,
    )


@server.tool()
async def generate_candidate_report(
    resume_text: str,
    job_description: str,
    ctx: Context,
) -> dict[str, Any]:
    """
    Generate a candidate-job match report.

    This is a composite MCP capability:
    1. inspect resume
    2. analyze job
    3. compare skills
    4. generate a deterministic assessment
    """

    api_key = _get_api_key(ctx)
    authorize(api_key, "generate_candidate_report")

    if not resume_text or not resume_text.strip():
        raise ToolError(
            "[INVALID_INPUT] resume_text cannot be empty"
        )

    if not job_description or not job_description.strip():
        raise ToolError(
            "[INVALID_INPUT] job_description cannot be empty"
        )

    request_id = _get_request_id(ctx)

    candidate = await _call_resume_service(
        {
            "resume_text": resume_text,
        },
        request_id,
    )

    job = await _call_job_service(
        {
            "job_description": job_description,
        },
        request_id,
    )

    candidate_skills = candidate.get("skills") or []
    required_skills = job.get("required_skills") or []

    if not required_skills:
        raise ToolError(
            "[INVALID_INPUT] Job contains no required skills"
        )

    match = await _call_matching_service(
        {
            "candidate_skills": candidate_skills,
            "required_skills": required_skills,
        },
        request_id,
    )

    candidate_experience = candidate.get("experience_years")
    required_experience = job.get("experience_required")

    if (
        candidate_experience is not None
        and required_experience is not None
    ):
        experience_met = (
            candidate_experience >= required_experience
        )
    else:
        experience_met = None

    match_percentage = match.get(
        "match_percentage",
        0,
    )

    if experience_met is True and match_percentage >= 80:
        assessment = (
            "Strong technical match. "
            "Experience requirement met."
        )
    elif match_percentage >= 60:
        assessment = (
            "Good technical match with some skill gaps."
        )
    else:
        assessment = (
            "Limited technical match. "
            "Several required skills are missing."
        )

    return {
        "candidate": {
            "name": candidate.get("candidate_name"),
            "email": candidate.get("email"),
            "phone": candidate.get("phone"),
            "experience_years": candidate_experience,
            "skills": candidate_skills,
        },
        "job": {
            "title": job.get("title"),
            "required_skills": required_skills,
            "experience_required": required_experience,
        },
        "skill_match": match,
        "experience": {
            "candidate_years": candidate_experience,
            "required_years": required_experience,
            "requirement_met": experience_met,
        },
        "overall_assessment": assessment,
        "correlation_id": request_id,
    }


@server.tool()
async def create_candidate_shortlist(
    job_description: str,
    resumes: list[str],
    ctx: Context,
) -> dict[str, Any]:
    """
    Create a ranked candidate shortlist.

    Candidates are ranked deterministically by:
    1. Higher skill match percentage
    2. Higher experience when skill match is tied
    """

    api_key = _get_api_key(ctx)
    authorize(api_key, "create_candidate_shortlist")

    if not job_description or not job_description.strip():
        raise ToolError(
            "[INVALID_INPUT] job_description cannot be empty"
        )

    if not resumes:
        raise ToolError(
            "[INVALID_INPUT] resumes cannot be empty"
        )

    request_id = _get_request_id(ctx)

    job = await _call_job_service(
        {
            "job_description": job_description,
        },
        request_id,
    )

    required_skills = job.get("required_skills") or []

    if not required_skills:
        raise ToolError(
            "[INVALID_INPUT] Job contains no required skills"
        )

    ranked_candidates: list[dict[str, Any]] = []

    for resume_text in resumes:
        if not resume_text or not str(resume_text).strip():
            raise ToolError(
                "[INVALID_INPUT] Every resume must contain text"
            )

        candidate_profile = await _call_resume_service(
            {
                "resume_text": resume_text,
            },
            request_id,
        )

        candidate_skills = candidate_profile.get("skills") or []

        match = await _call_matching_service(
            {
                "candidate_skills": candidate_skills,
                "required_skills": required_skills,
            },
            request_id,
        )

        experience = candidate_profile.get(
            "experience_years"
        )

        sort_experience = (
            experience if experience is not None else 0
        )

        ranked_candidates.append(
            {
                "name": candidate_profile.get(
                    "candidate_name"
                ),
                "email": candidate_profile.get(
                    "email"
                ),
                "match_percentage": match.get(
                    "match_percentage",
                    0,
                ),
                "matched_skills": match.get(
                    "matched_skills",
                    [],
                ),
                "missing_skills": match.get(
                    "missing_skills",
                    [],
                ),
                "experience_years": experience,
                "_sort_experience": sort_experience,
            }
        )

    ranked_candidates.sort(
        key=lambda candidate: (
            -float(
                candidate.get(
                    "match_percentage",
                    0,
                )
            ),
            -int(
                candidate.get(
                    "_sort_experience",
                    0,
                )
            ),
        )
    )

    for rank, candidate in enumerate(
        ranked_candidates,
        start=1,
    ):
        candidate["rank"] = rank
        candidate.pop("_sort_experience", None)

    return {
        "job": {
            "title": job.get("title"),
            "required_skills": required_skills,
            "experience_required": job.get(
                "experience_required"
            ),
        },
        "total_candidates": len(ranked_candidates),
        "candidates": ranked_candidates,
        "correlation_id": request_id,
    }


@server.tool()
async def get_github_profile(
    username: str,
    ctx: Context,
) -> dict[str, Any]:
    """
    Fetch GitHub profile and public repository intelligence
    for a candidate.
    """

    api_key = _get_api_key(ctx)
    authorize(api_key, "get_github_profile")

    if not username or not username.strip():
        raise ToolError(
            "[INVALID_INPUT] GitHub username cannot be empty"
        )

    request_id = _get_request_id(ctx)

    try:
        user = await get_user(username)
        repositories = await get_user_repositories(username)

        repo_data: list[dict[str, Any]] = []

        for repo in repositories:
            repo_data.append(
                {
                    "name": repo.get("name"),
                    "description": repo.get("description"),
                    "language": repo.get("language"),
                    "html_url": repo.get("html_url"),
                    "topics": repo.get("topics", []),
                    "stars": repo.get(
                        "stargazers_count",
                        0,
                    ),
                    "forks": repo.get(
                        "forks_count",
                        0,
                    ),
                }
            )

        return {
            "username": user.get("login"),
            "name": user.get("name"),
            "bio": user.get("bio"),
            "public_repositories": user.get(
                "public_repos",
                0,
            ),
            "followers": user.get(
                "followers",
                0,
            ),
            "following": user.get(
                "following",
                0,
            ),
            "profile_url": user.get("html_url"),
            "repositories": repo_data,
            "correlation_id": request_id,
        }

    except GitHubClientError as exc:
        raise ToolError(
            f"[{exc.code}] {exc.message}"
        )


if __name__ == "__main__":
    server.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8000,
    )