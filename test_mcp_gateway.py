"""Automated test suite for Talent Intelligence MCP Gateway using official MCP Python Client."""

import asyncio
import json
import sys
from mcp import Client


async def run_tests():
    print("=" * 60)
    print("TALENT INTELLIGENCE MCP GATEWAY - PROTOCOL VERIFICATION")
    print("=" * 60)

    server_url = "http://127.0.0.1:8000/mcp"
    print(f"\n[1] Connecting to MCP Gateway at {server_url} ...")

    async with Client(server_url) as client:
        # -------------------------------------------------------------
        # TEST 1: Tool Discovery (tools/list)
        # -------------------------------------------------------------
        print("\n[2] Executing tools/list ...")
        list_result = await client.list_tools()
        tools = list_result.tools
        tool_names = [t.name for t in tools]
        print(f"    Discovered {len(tools)} tools: {tool_names}")

        expected_tools = ["inspect_resume", "analyze_job", "compare_skills"]
        assert sorted(tool_names) == sorted(expected_tools), f"Expected tools {expected_tools}, got {tool_names}"

        for tool in tools:
            print(f"\n    --- Tool: {tool.name} ---")
            print(f"    Description : {tool.description}")
            print(f"    Input Schema: {json.dumps(tool.input_schema, indent=6)}")
            assert tool.description, f"Tool {tool.name} missing description"
            assert tool.input_schema.get("type") == "object", "Input schema must be object"
            assert "required" in tool.input_schema, "Input schema must have required fields"

        # -------------------------------------------------------------
        # TEST 2: Tool Call: inspect_resume (tools/call)
        # -------------------------------------------------------------
        print("\n[3] Executing tools/call: inspect_resume ...")
        resume_input = {
            "resume_text": (
                "Alex Johnson is a backend developer with 4 years of experience. "
                "He has worked with Python, SQL, FastAPI and Docker. He completed B.Tech."
            )
        }
        res_resume = await client.call_tool("inspect_resume", resume_input)
        print(f"    is_error: {res_resume.is_error}")
        assert not res_resume.is_error, "inspect_resume failed"
        
        # Check structured content
        resume_data = res_resume.structured_content.get("result", {})
        print(f"    Returned Data: {json.dumps(resume_data, indent=6)}")
        assert resume_data["candidate_name"] == "Alex Johnson"
        assert "Python" in resume_data["skills"]
        assert resume_data["experience_years"] == 4
        assert resume_data["education"] == "B.Tech"

        # -------------------------------------------------------------
        # TEST 3: Tool Call: analyze_job (tools/call)
        # -------------------------------------------------------------
        print("\n[4] Executing tools/call: analyze_job ...")
        job_input = {
            "job_description": (
                "We are looking for a Backend Software Engineer with 3+ years of experience. "
                "Required skills: Python, SQL and REST API."
            )
        }
        res_job = await client.call_tool("analyze_job", job_input)
        print(f"    is_error: {res_job.is_error}")
        assert not res_job.is_error, "analyze_job failed"

        job_data = res_job.structured_content.get("result", {})
        print(f"    Returned Data: {json.dumps(job_data, indent=6)}")
        assert job_data["title"] == "Backend Software Engineer"
        assert "Python" in job_data["required_skills"]
        assert job_data["experience_required"] == 3

        # -------------------------------------------------------------
        # TEST 4: Tool Call: compare_skills (tools/call)
        # -------------------------------------------------------------
        print("\n[5] Executing tools/call: compare_skills ...")
        matching_input = {
            "candidate_skills": ["Python", "SQL"],
            "required_skills": ["Python", "SQL", "REST API"]
        }
        res_match = await client.call_tool("compare_skills", matching_input)
        print(f"    is_error: {res_match.is_error}")
        assert not res_match.is_error, "compare_skills failed"

        match_data = res_match.structured_content.get("result", {})
        print(f"    Returned Data: {json.dumps(match_data, indent=6)}")
        assert match_data["matched"] == ["Python", "SQL"]
        assert match_data["missing"] == ["REST API"]
        assert match_data["match_percentage"] == 66.67

        # -------------------------------------------------------------
        # TEST 5: Error Translation (Invalid input)
        # -------------------------------------------------------------
        print("\n[6] Testing Error Translation (invalid empty input) ...")
        res_err = await client.call_tool("inspect_resume", {"resume_text": ""})
        print(f"    is_error: {res_err.is_error}")
        assert res_err.is_error, "Expected tool error for empty resume_text"
        err_text = res_err.content[0].text if res_err.content else ""
        print(f"    Error message received: {err_text}")
        assert "[INVALID_INPUT]" in err_text, f"Expected [INVALID_INPUT] code in error message: {err_text}"
        assert "Traceback" not in err_text, "Error should not leak raw stack trace"

        print("\n" + "=" * 60)
        print("ALL MCP GATEWAY TESTS PASSED SUCCESSFULLY!")
        print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(run_tests())
    except Exception as exc:
        print(f"\nTEST RUNNER ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
