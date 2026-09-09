"""
End-to-end protocol test suite for the Talent Intelligence MCP Gateway.

Verifies:
- MCP session initialization
- Exactly 5 discovered MCP tools
- MCP tool input schemas
- API-key authentication transport
- Authorization / entitlement checks
- 3 atomic MCP tools
- 2 composite MCP tools
- Real input-driven resume parsing
- Real input-driven job parsing
- Deterministic skill matching
- Deterministic shortlist ranking
- Deterministic tie-breaking
- Validation errors
- No fabricated candidate data

Architecture under test:

MCP Client
    |
    v
MCP Gateway :8000
    |
    +--> Resume API   :8001
    +--> Job API      :8002
    +--> Matching API :8003
"""

import asyncio
import sys
import traceback

import httpx
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client


# ============================================================================
# Configuration
# ============================================================================

SERVER_URL = "http://127.0.0.1:8000/mcp"

DEMO_API_KEY = "demo-client-key"
READONLY_API_KEY = "readonly-client-key"


# ============================================================================
# Test data
# ============================================================================

RESUME_TEXT = (
    "Candidate Name: Vedant Lodhi\n"
    "Email: vedant@example.com\n"
    "Phone: +91-9999999999\n"
    "Location: India\n\n"
    "Python backend developer with 4 years "
    "of professional experience.\n\n"
    "Skills: Python, SQL, FastAPI, Docker, AWS.\n\n"
    "Education: B.Tech in Computer Science."
)


JOB_DESCRIPTION = (
    "Job Title: Python Backend Developer\n\n"
    "We are looking for a Python developer "
    "with 3+ years of professional experience.\n\n"
    "Required skills: Python, FastAPI, SQL, "
    "PostgreSQL, Docker and AWS.\n\n"
    "Experience building REST APIs is required."
)


# ============================================================================
# Helper functions
# ============================================================================


def print_section(title: str):
    """Print a readable test section."""

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def print_mcp_error(tool_name: str, result):
    """Print detailed MCP error information."""

    print()
    print(f"MCP ERROR from tool: {tool_name}")
    print(f"is_error: {result.is_error}")

    print("content:")

    if result.content:
        for item in result.content:
            print(f"    {item}")
    else:
        print("    <empty>")

    print("structured_content:")
    print(f"    {result.structured_content}")

    print()


def assert_tool_success(tool_name: str, result):
    """Fail with useful diagnostic information if a tool returns an error."""

    if result.is_error:
        print_mcp_error(tool_name, result)

        raise AssertionError(
            f"{tool_name} returned an MCP error"
        )


def get_result_data(result):
    """
    Extract semantic data returned by an MCP tool.

    The gateway should return business/capability data rather than
    exposing the internal REST success/data/error envelope.
    """

    structured = result.structured_content or {}

    if not isinstance(structured, dict):
        return {}

    result_data = structured.get("result")

    if isinstance(result_data, dict):
        return result_data

    return structured


def assert_non_empty(value, field_name: str):
    """Assert that a value is not None or empty."""

    assert value not in (None, "", [], {}), (
        f"{field_name} should not be empty"
    )


# ============================================================================
# MCP session helper
# ============================================================================


async def open_mcp_session(api_key: str):
    """
    Open an authenticated Streamable HTTP MCP session.

    The API key is placed on the HTTP transport so that the
    MCP Gateway can authenticate the calling client.
    """

    http_client = httpx.AsyncClient(
        headers={
            "X-API-Key": api_key,
        },
        timeout=30.0,
    )

    stream_context = streamable_http_client(
        SERVER_URL,
        http_client=http_client,
    )

    read_stream, write_stream = (
        await stream_context.__aenter__()
    )

    client = ClientSession(
        read_stream,
        write_stream,
    )

    await client.__aenter__()

    await client.initialize()

    return (
        http_client,
        stream_context,
        client,
    )


async def close_mcp_session(
    http_client,
    stream_context,
    client,
):
    """Close an MCP session cleanly."""

    await client.__aexit__(
        None,
        None,
        None,
    )

    await stream_context.__aexit__(
        None,
        None,
        None,
    )

    await http_client.aclose()


# ============================================================================
# Main test runner
# ============================================================================


async def run_tests():

    print("=" * 70)
    print("TALENT INTELLIGENCE MCP GATEWAY")
    print("END-TO-END PROTOCOL VERIFICATION")
    print("=" * 70)

    # ========================================================================
    # TEST 1
    # MCP CONNECTION + TOOL DISCOVERY
    # ========================================================================

    print_section(
        "TEST 1 - MCP CONNECTION AND TOOL DISCOVERY"
    )

    print(
        f"Connecting to MCP Gateway: {SERVER_URL}"
    )

    (
        http_client,
        stream_context,
        client,
    ) = await open_mcp_session(
        DEMO_API_KEY
    )

    try:

        print("MCP session initialized.")

        list_result = await client.list_tools()

        tools = list_result.tools

        tool_names = [
            tool.name
            for tool in tools
        ]

        print(
            f"Discovered {len(tools)} tools:"
        )

        for tool_name in tool_names:
            print(
                f"    - {tool_name}"
            )

        expected_tools = [
            "inspect_resume",
            "analyze_job",
            "compare_skills",
            "generate_candidate_report",
            "create_candidate_shortlist",
	    "get_github_profile",
        ]

        assert len(tools) == 6, (
    	   f"Expected exactly 6 tools, got {len(tools)}"
	)

        assert sorted(tool_names) == sorted(
            expected_tools
        ), (
            f"Expected tools:\n"
            f"{expected_tools}\n"
            f"Got:\n"
            f"{tool_names}"
        )

        # Validate MCP schemas.
        for tool in tools:

            print()
            print(
                f"    Tool: {tool.name}"
            )

            assert tool.description, (
                f"{tool.name} is missing description"
            )

            assert (
                tool.input_schema.get("type")
                == "object"
            ), (
                f"{tool.name} input schema "
                f"must be an object"
            )

            assert (
                "required"
                in tool.input_schema
            ), (
                f"{tool.name} schema must contain "
                f"required fields"
            )

        print(
            "\nTool discovery PASSED."
        )

        # ====================================================================
        # TEST 2
        # inspect_resume
        # ====================================================================

        print_section(
            "TEST 2 - inspect_resume"
        )

        result = await client.call_tool(
            "inspect_resume",
            {
                "resume_text": RESUME_TEXT,
            },
        )

        assert_tool_success(
            "inspect_resume",
            result,
        )

        resume_data = get_result_data(
            result
        )

        print(
            f"Candidate Name : "
            f"{resume_data.get('candidate_name')}"
        )

        print(
            f"Email          : "
            f"{resume_data.get('email')}"
        )

        print(
            f"Phone          : "
            f"{resume_data.get('phone')}"
        )

        print(
            f"Skills         : "
            f"{resume_data.get('skills')}"
        )

        print(
            f"Experience     : "
            f"{resume_data.get('experience_years')}"
        )

        print(
            f"Education      : "
            f"{resume_data.get('education')}"
        )

        # Required fields must exist.
        assert "candidate_name" in resume_data
        assert "skills" in resume_data
        assert "experience_years" in resume_data

        # Candidate identity must come from the input.
        assert (
            resume_data["candidate_name"]
            == "Vedant Lodhi"
        )

        assert (
            resume_data["email"]
            == "vedant@example.com"
        )

        assert (
            resume_data["phone"]
            == "+91-9999999999"
        )

        # Experience must come from the input.
        assert (
            resume_data["experience_years"]
            == 4
        )

        # Skills must come from the input.
        for skill in [
            "Python",
            "SQL",
            "FastAPI",
            "Docker",
            "AWS",
        ]:
            assert skill in (
                resume_data["skills"]
            ), (
                f"{skill} was not extracted "
                f"from resume"
            )

        print(
            "\ninspect_resume PASSED."
        )

        # ====================================================================
        # TEST 3
        # analyze_job
        # ====================================================================

        print_section(
            "TEST 3 - analyze_job"
        )

        result = await client.call_tool(
            "analyze_job",
            {
                "job_description":
                    JOB_DESCRIPTION,
            },
        )

        assert_tool_success(
            "analyze_job",
            result,
        )

        job_data = get_result_data(
            result
        )

        print(
            f"Job Title      : "
            f"{job_data.get('title')}"
        )

        print(
            f"Required Skills: "
            f"{job_data.get('required_skills')}"
        )

        print(
            f"Experience     : "
            f"{job_data.get('experience_required')}"
        )

        print(
            f"Description Len: "
            f"{job_data.get('description_length')}"
        )

        assert "title" in job_data

        assert (
            job_data["title"]
            == "Python Backend Developer"
        )

        assert (
            job_data["experience_required"]
            == 3
        )

        for skill in [
            "Python",
            "FastAPI",
            "SQL",
            "PostgreSQL",
            "Docker",
            "AWS",
        ]:
            assert skill in (
                job_data["required_skills"]
            ), (
                f"{skill} missing from "
                f"job analysis"
            )

        assert (
            job_data["description_length"]
            > 0
        )

        print(
            "\nanalyze_job PASSED."
        )

        # ====================================================================
        # TEST 4
        # compare_skills
        # ====================================================================

        print_section(
            "TEST 4 - compare_skills"
        )

        result = await client.call_tool(
            "compare_skills",
            {
                "candidate_skills": [
                    "Python",
                    "SQL",
                    "FastAPI",
                ],
                "required_skills": [
                    "Python",
                    "SQL",
                    "FastAPI",
                    "AWS",
                ],
            },
        )

        assert_tool_success(
            "compare_skills",
            result,
        )

        match_data = get_result_data(
            result
        )

        print(
            f"Matched Skills  : "
            f"{match_data.get('matched')}"
        )

        print(
            f"Missing Skills  : "
            f"{match_data.get('missing')}"
        )

        print(
            f"Match Percentage: "
            f"{match_data.get('match_percentage')}%"
        )

        assert (
            match_data["matched"]
            == [
                "Python",
                "SQL",
                "FastAPI",
            ]
        )

        assert (
            match_data["missing"]
            == ["AWS"]
        )

        assert (
            match_data["match_percentage"]
            == 75.0
        )

        print(
            "\ncompare_skills PASSED."
        )

        # ====================================================================
        # TEST 5
        # generate_candidate_report
        # ====================================================================

        print_section(
            "TEST 5 - generate_candidate_report"
        )

        result = await client.call_tool(
            "generate_candidate_report",
            {
                "resume_text":
                    RESUME_TEXT,
                "job_description":
                    JOB_DESCRIPTION,
            },
        )

        assert_tool_success(
            "generate_candidate_report",
            result,
        )

        report_data = get_result_data(
            result
        )

        candidate = report_data.get(
            "candidate",
            {},
        )

        report_job = report_data.get(
            "job",
            {},
        )

        skill_match = report_data.get(
            "skill_match",
            {},
        )

        print(
            f"Candidate Name : "
            f"{candidate.get('name')}"
        )

        print(
            f"Candidate Skills: "
            f"{candidate.get('skills')}"
        )

        print(
            f"Job Title      : "
            f"{report_job.get('title')}"
        )

        print(
            f"Matched Skills : "
            f"{skill_match.get('matched')}"
        )

        print(
            f"Missing Skills : "
            f"{skill_match.get('missing')}"
        )

        print(
            f"Match %        : "
            f"{skill_match.get('match_percentage')}"
        )

        print(
            f"Assessment     : "
            f"{report_data.get('overall_assessment')}"
        )

        assert "candidate" in report_data
        assert "job" in report_data
        assert "skill_match" in report_data

        assert_non_empty(
            candidate.get("name"),
            "report candidate name",
        )

        # Report identity must come from Resume API.
        assert (
            candidate["name"]
            == resume_data["candidate_name"]
        )

        assert (
            candidate["skills"]
            == resume_data["skills"]
        )

        # Report job must come from Job API.
        assert (
            report_job["title"]
            == job_data["title"]
        )

        assert (
            report_job["required_skills"]
            == job_data["required_skills"]
        )

        # Candidate has:
        #
        # Python
        # SQL
        # FastAPI
        # Docker
        # AWS
        #
        # Job requires:
        #
        # Python
        # FastAPI
        # SQL
        # PostgreSQL
        # Docker
        # AWS
        #
        # 5 / 6 = 83.33%

        assert (
            skill_match["match_percentage"]
            == 83.33
        )

        assert (
            "PostgreSQL"
            in skill_match["missing"]
        )

        assert_non_empty(
            report_data.get(
                "overall_assessment"
            ),
            "overall_assessment",
        )

        print(
            "\ngenerate_candidate_report PASSED."
        )

        # ====================================================================
        # TEST 6
        # create_candidate_shortlist
        # ====================================================================

        print_section(
            "TEST 6 - create_candidate_shortlist"
        )

        resumes = [
            (
                "Candidate Name: Alpha\n"
                "Experience: 5 years.\n"
                "Skills: Python, SQL, FastAPI, Docker."
            ),
            (
                "Candidate Name: Beta\n"
                "Experience: 2 years.\n"
                "Skills: Python."
            ),
            (
                "Candidate Name: Gamma\n"
                "Experience: 6 years.\n"
                "Skills: Python, SQL, FastAPI, "
                "PostgreSQL, Docker and AWS."
            ),
        ]

        result = await client.call_tool(
            "create_candidate_shortlist",
            {
                "job_description":
                    JOB_DESCRIPTION,
                "resumes":
                    resumes,
            },
        )

        assert_tool_success(
            "create_candidate_shortlist",
            result,
        )

        shortlist_data = get_result_data(
            result
        )

        candidates = shortlist_data.get(
            "candidates",
            [],
        )

        print(
            f"Total Candidates: "
            f"{shortlist_data.get('total_candidates')}"
        )

        for candidate in candidates:

            print(
                f"Rank {candidate['rank']}: "
                f"{candidate['name']} | "
                f"Match: "
                f"{candidate['match_percentage']}% | "
                f"Experience: "
                f"{candidate['experience_years']} years"
            )

        assert (
            shortlist_data[
                "total_candidates"
            ]
            == 3
        )

        assert len(candidates) == 3

        # --------------------------------------------------------------------
        # Gamma
        # --------------------------------------------------------------------

        assert (
            candidates[0]["name"]
            == "Gamma"
        )

        assert (
            candidates[0]["rank"]
            == 1
        )

        assert (
            candidates[0]["match_percentage"]
            == 100.0
        )

        assert (
            candidates[0]["experience_years"]
            == 6
        )

        # --------------------------------------------------------------------
        # Alpha
        # --------------------------------------------------------------------

        assert (
            candidates[1]["name"]
            == "Alpha"
        )

        assert (
            candidates[1]["rank"]
            == 2
        )

        assert (
            candidates[1]["match_percentage"]
            == 66.67
        )

        assert (
            candidates[1]["experience_years"]
            == 5
        )

        # --------------------------------------------------------------------
        # Beta
        # --------------------------------------------------------------------

        assert (
            candidates[2]["name"]
            == "Beta"
        )

        assert (
            candidates[2]["rank"]
            == 3
        )

        assert (
            candidates[2]["match_percentage"]
            == 16.67
        )

        assert (
            candidates[2]["experience_years"]
            == 2
        )

        # Overall ranking order.
        assert (
            candidates[0]["match_percentage"]
            >= candidates[1]["match_percentage"]
        )

        assert (
            candidates[1]["match_percentage"]
            >= candidates[2]["match_percentage"]
        )

        print(
            "\ncreate_candidate_shortlist PASSED."
        )

        # ====================================================================
        # TEST 7
        # DETERMINISTIC TIE-BREAKING
        # ====================================================================

        print_section(
            "TEST 7 - DETERMINISTIC TIE-BREAKING"
        )

        tie_resumes = [
            (
                "Candidate Name: Delta\n"
                "Experience: 4 years.\n"
                "Skills: Python and SQL."
            ),
            (
                "Candidate Name: Epsilon\n"
                "Experience: 8 years.\n"
                "Skills: Python and SQL."
            ),
        ]

        result = await client.call_tool(
            "create_candidate_shortlist",
            {
                "job_description": (
                    "Job Title: Backend Developer\n"
                    "Role requiring Python and SQL."
                ),
                "resumes":
                    tie_resumes,
            },
        )

        assert_tool_success(
            "create_candidate_shortlist "
            "(tie-breaking)",
            result,
        )

        tie_data = get_result_data(
            result
        )

        tie_candidates = tie_data.get(
            "candidates",
            [],
        )

        assert len(tie_candidates) == 2

        print(
            f"Rank 1: "
            f"{tie_candidates[0]['name']} | "
            f"{tie_candidates[0]['experience_years']} years"
        )

        print(
            f"Rank 2: "
            f"{tie_candidates[1]['name']} | "
            f"{tie_candidates[1]['experience_years']} years"
        )

        # Both candidates have identical skills.
        assert (
            tie_candidates[0][
                "match_percentage"
            ]
            == tie_candidates[1][
                "match_percentage"
            ]
        )

        # Higher experience wins.
        assert (
            tie_candidates[0]["name"]
            == "Epsilon"
        )

        assert (
            tie_candidates[0]["experience_years"]
            == 8
        )

        assert (
            tie_candidates[0]["rank"]
            == 1
        )

        assert (
            tie_candidates[1]["name"]
            == "Delta"
        )

        assert (
            tie_candidates[1]["experience_years"]
            == 4
        )

        assert (
            tie_candidates[1]["rank"]
            == 2
        )

        print(
            "\nDeterministic tie-breaking PASSED."
        )

        # ====================================================================
        # TEST 8
        # INPUT VALIDATION
        # ====================================================================

        print_section(
            "TEST 8 - INPUT VALIDATION"
        )

        # --------------------------------------------------------------------
        # Empty resume
        # --------------------------------------------------------------------

        result = await client.call_tool(
            "inspect_resume",
            {
                "resume_text": "",
            },
        )

        assert result.is_error

        error_text = (
            result.content[0].text
        )

        print(
            f"Empty resume: {error_text}"
        )

        assert (
            "[INVALID_INPUT]"
            in error_text
        )

        # --------------------------------------------------------------------
        # Empty job
        # --------------------------------------------------------------------

        result = await client.call_tool(
            "analyze_job",
            {
                "job_description": "",
            },
        )

        assert result.is_error

        error_text = (
            result.content[0].text
        )

        print(
            f"Empty job: {error_text}"
        )

        assert (
            "[INVALID_INPUT]"
            in error_text
        )

        # --------------------------------------------------------------------
        # Empty candidate skills
        # --------------------------------------------------------------------

        result = await client.call_tool(
            "compare_skills",
            {
                "candidate_skills": [],
                "required_skills": [
                    "Python",
                ],
            },
        )

        assert result.is_error

        error_text = (
            result.content[0].text
        )

        print(
            f"Empty candidate skills: "
            f"{error_text}"
        )

        assert (
            "[INVALID_INPUT]"
            in error_text
        )

        print(
            "\nInput validation PASSED."
        )

    finally:

        await close_mcp_session(
            http_client,
            stream_context,
            client,
        )

    # ========================================================================
    # TEST 9
    # AUTHENTICATION + AUTHORIZATION
    # ========================================================================

    print_section(
        "TEST 9 - AUTHENTICATION AND AUTHORIZATION"
    )

    # ------------------------------------------------------------------------
    # readonly-client-key
    # ------------------------------------------------------------------------

    (
        readonly_http,
        readonly_stream_context,
        readonly_client,
    ) = await open_mcp_session(
        READONLY_API_KEY
    )

    try:

        # Atomic capability should be allowed.
        result = await readonly_client.call_tool(
            "inspect_resume",
            {
                "resume_text":
                    RESUME_TEXT,
            },
        )

        assert_tool_success(
            "readonly inspect_resume",
            result,
        )

        print(
            "readonly-client-key -> "
            "inspect_resume: ALLOWED"
        )

        # Another atomic capability should also be allowed.
        result = await readonly_client.call_tool(
            "analyze_job",
            {
                "job_description":
                    JOB_DESCRIPTION,
            },
        )

        assert_tool_success(
            "readonly analyze_job",
            result,
        )

        print(
            "readonly-client-key -> "
            "analyze_job: ALLOWED"
        )

        # Composite capability should be denied.
        result = await readonly_client.call_tool(
            "generate_candidate_report",
            {
                "resume_text":
                    RESUME_TEXT,
                "job_description":
                    JOB_DESCRIPTION,
            },
        )

        assert result.is_error

        error_text = (
            result.content[0].text
        )

        print(
            "readonly-client-key -> "
            "generate_candidate_report:"
        )

        print(
            f"    {error_text}"
        )

        assert (
            "[AUTHORIZATION_DENIED]"
            in error_text
        )

        print(
            "Authorization denial PASSED."
        )

    finally:

        await close_mcp_session(
            readonly_http,
            readonly_stream_context,
            readonly_client,
        )

    # ========================================================================
    # FINAL RESULT
    # ========================================================================

    print()
    print("=" * 70)
    print("ALL MCP GATEWAY TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


# ============================================================================
# Script entry point
# ============================================================================


if __name__ == "__main__":

    try:

        asyncio.run(
            run_tests()
        )

    except Exception as exc:

        print(
            "\nTEST RUNNER ERROR:",
            file=sys.stderr,
        )

        print(
            repr(exc),
            file=sys.stderr,
        )

        traceback.print_exc()

        # --------------------------------------------------------------------
        # ExceptionGroup / TaskGroup diagnostics
        # --------------------------------------------------------------------

        if hasattr(
            exc,
            "exceptions",
        ):

            print(
                "\nSUB-EXCEPTIONS:",
                file=sys.stderr,
            )

            for sub_exc in exc.exceptions:

                print(
                    repr(sub_exc),
                    file=sys.stderr,
                )

                traceback.print_exception(
                    type(sub_exc),
                    sub_exc,
                    sub_exc.__traceback__,
                )

                if hasattr(
                    sub_exc,
                    "exceptions",
                ):

                    for nested_exc in (
                        sub_exc.exceptions
                    ):

                        print(
                            f"    Nested: "
                            f"{repr(nested_exc)}",
                            file=sys.stderr,
                        )

                        traceback.print_exception(
                            type(nested_exc),
                            nested_exc,
                            nested_exc.__traceback__,
                        )

        sys.exit(1)