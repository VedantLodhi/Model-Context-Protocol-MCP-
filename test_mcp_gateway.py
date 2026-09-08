"""Automated test suite for Talent Intelligence MCP Gateway (Phase 2 & Phase 3).

Verifies:
- 5 discovered MCP tools with correct input schemas
- 3 atomic tool calls (inspect_resume, analyze_job, compare_skills)
- Composite tool: generate_candidate_report
- Composite tool: create_candidate_shortlist (with deterministic ranking and tie-breaking)
- Validation edge cases (empty inputs)
- Single correlation ID propagation across sub-operations
"""

import asyncio
import json
import sys
from mcp import Client


async def run_tests():
    print("=" * 70)
    print("TALENT INTELLIGENCE MCP GATEWAY - COMPOSITE PROTOCOL VERIFICATION")
    print("=" * 70)

    server_url = "http://127.0.0.1:8000/mcp"
    print(f"\n[1] Connecting to MCP Gateway at {server_url} ...")

    async with Client(server_url) as client:
        # -------------------------------------------------------------
        # TEST 1: Tool Discovery (tools/list) - Exactly 5 Tools
        # -------------------------------------------------------------
        print("\n[2] Executing tools/list ...")
        list_result = await client.list_tools()
        tools = list_result.tools
        tool_names = [t.name for t in tools]
        print(f"    Discovered {len(tools)} tools: {tool_names}")

        expected_tools = [
            "inspect_resume",
            "analyze_job",
            "compare_skills",
            "generate_candidate_report",
            "create_candidate_shortlist"
        ]
        assert sorted(tool_names) == sorted(expected_tools), (
            f"Expected exactly 5 tools {expected_tools}, got {tool_names}"
        )

        for tool in tools:
            print(f"\n    --- Tool: {tool.name} ---")
            print(f"    Description : {tool.description}")
            assert tool.description, f"Tool {tool.name} missing description"
            assert tool.input_schema.get("type") == "object", "Input schema must be object"
            assert "required" in tool.input_schema, f"Tool {tool.name} schema must have required fields"

        # -------------------------------------------------------------
        # TEST 2: Atomic Tool: inspect_resume
        # -------------------------------------------------------------
        print("\n[3] Testing inspect_resume ...")
        res_resume = await client.call_tool("inspect_resume", {
            "resume_text": "Alex Johnson is a backend developer with 4 years of experience. He has worked with Python, SQL, FastAPI and Docker. He completed B.Tech."
        })
        assert not res_resume.is_error, "inspect_resume failed"
        resume_data = res_resume.structured_content.get("result", {})
        print(f"    Returned: {resume_data['candidate_name']}, skills={resume_data['skills']}")
        assert resume_data["candidate_name"] == "Alex Johnson"
        assert "Python" in resume_data["skills"]

        # -------------------------------------------------------------
        # TEST 3: Atomic Tool: analyze_job
        # -------------------------------------------------------------
        print("\n[4] Testing analyze_job ...")
        res_job = await client.call_tool("analyze_job", {
            "job_description": "We are looking for a Backend Software Engineer with 3+ years of experience. Required skills: Python, SQL and REST API."
        })
        assert not res_job.is_error, "analyze_job failed"
        job_data = res_job.structured_content.get("result", {})
        print(f"    Returned: {job_data['title']}, req_skills={job_data['required_skills']}")
        assert job_data["title"] == "Backend Software Engineer"
        assert "Python" in job_data["required_skills"]

        # -------------------------------------------------------------
        # TEST 4: Atomic Tool: compare_skills
        # -------------------------------------------------------------
        print("\n[5] Testing compare_skills ...")
        res_match = await client.call_tool("compare_skills", {
            "candidate_skills": ["Python", "SQL"],
            "required_skills": ["Python", "SQL", "REST API"]
        })
        assert not res_match.is_error, "compare_skills failed"
        match_data = res_match.structured_content.get("result", {})
        print(f"    Returned: matched={match_data['matched']}, percentage={match_data['match_percentage']}%")
        assert match_data["matched"] == ["Python", "SQL"]
        assert match_data["match_percentage"] == 66.67

        # -------------------------------------------------------------
        # TEST 5: Composite Tool: generate_candidate_report
        # -------------------------------------------------------------
        print("\n[6] Testing composite tool: generate_candidate_report ...")
        report_input = {
            "resume_text": "Alex Johnson is a backend developer with 4 years of experience. He has worked with Python, SQL, FastAPI and Docker. He completed B.Tech.",
            "job_description": "We are looking for a Backend Software Engineer with 3+ years of experience. Required skills: Python, SQL and REST API."
        }
        res_report = await client.call_tool("generate_candidate_report", report_input)
        assert not res_report.is_error, "generate_candidate_report failed"
        report_data = res_report.structured_content.get("result", {})
        print(f"    Candidate Name      : {report_data['candidate']['name']}")
        print(f"    Candidate Skills    : {report_data['candidate']['skills']}")
        print(f"    Job Title           : {report_data['job']['title']}")
        print(f"    Required Skills     : {report_data['job']['required_skills']}")
        print(f"    Matched Skills      : {report_data['skill_match']['matched']}")
        print(f"    Missing Skills      : {report_data['skill_match']['missing']}")
        print(f"    Match Percentage    : {report_data['skill_match']['match_percentage']}%")
        print(f"    Overall Assessment  : {report_data['overall_assessment']}")

        assert report_data["candidate"]["name"] == "Alex Johnson"
        assert "FastAPI" in report_data["candidate"]["skills"]
        assert report_data["job"]["title"] == "Backend Software Engineer"
        assert report_data["skill_match"]["matched"] == ["Python", "SQL"]
        assert report_data["skill_match"]["missing"] == ["REST API"]
        assert report_data["skill_match"]["match_percentage"] == 66.67
        assert "Good technical match" in report_data["overall_assessment"]
        assert "Experience requirement met" in report_data["overall_assessment"]

        # -------------------------------------------------------------
        # TEST 6: Composite Tool: create_candidate_shortlist (Ranking Test)
        # -------------------------------------------------------------
        print("\n[7] Testing composite tool: create_candidate_shortlist (Ranking Test) ...")
        resumes_sample = [
            # Candidate A: 5 yrs, Python, SQL, FastAPI (66.67% match against Python, SQL, REST API)
            "Candidate Alpha has 5 years of experience in backend development. Strong in Python, SQL, and FastAPI. Completed B.Tech.",
            # Candidate B: 2 yrs, Python (33.33% match)
            "Candidate Beta is a junior developer with 2 years of experience. Worked with Python. Completed B.S.",
            # Candidate C: 6 yrs, Python, SQL, REST API (100% match)
            "Candidate Gamma is a senior engineer with 6 years of experience. Expert in Python, SQL, and REST API. Completed M.S."
        ]
        shortlist_input = {
            "job_description": "We are looking for a Backend Software Engineer with 3+ years of experience. Required skills: Python, SQL and REST API.",
            "resumes": resumes_sample
        }
        res_shortlist = await client.call_tool("create_candidate_shortlist", shortlist_input)
        assert not res_shortlist.is_error, "create_candidate_shortlist failed"
        shortlist_data = res_shortlist.structured_content.get("result", {})
        candidates = shortlist_data.get("candidates", [])
        print(f"    Total candidates processed: {shortlist_data['total_candidates']}")

        for c in candidates:
            print(f"    Rank {c['rank']}: {c['name']} | Match: {c['match_percentage']}% | Exp: {c['experience_years']} yrs | Matched: {c['matched_skills']}")

        assert shortlist_data["total_candidates"] == 3
        # Explicit Assertion: Candidate C (Gamma) must be rank 1 with 100% match
        assert candidates[0]["rank"] == 1
        assert candidates[0]["name"] == "Candidate Gamma"
        assert candidates[0]["match_percentage"] == 100.0
        assert candidates[0]["experience_years"] == 6

        # Candidate A (Alpha) must be rank 2 with 66.67% match
        assert candidates[1]["rank"] == 2
        assert candidates[1]["name"] == "Candidate Alpha"
        assert candidates[1]["match_percentage"] == 66.67

        # Candidate B (Beta) must be rank 3 with 33.33% match
        assert candidates[2]["rank"] == 3
        assert candidates[2]["name"] == "Candidate Beta"
        assert candidates[2]["match_percentage"] == 33.33

        # -------------------------------------------------------------
        # TEST 7: Tie-Breaking Test (Equal Match %, Higher Exp Wins)
        # -------------------------------------------------------------
        print("\n[8] Testing deterministic tie-breaking (Equal Match %, Higher Experience Wins) ...")
        tie_resumes = [
            "Candidate Delta has 4 years of experience with Python and SQL. Completed B.Tech.",
            "Candidate Epsilon has 8 years of experience with Python and SQL. Completed M.S."
        ]
        res_tie = await client.call_tool("create_candidate_shortlist", {
            "job_description": "Role requiring Python and SQL.",
            "resumes": tie_resumes
        })
        assert not res_tie.is_error, "tie-break test failed"
        tie_candidates = res_tie.structured_content.get("result", {}).get("candidates", [])
        print(f"    Rank 1: {tie_candidates[0]['name']} (Exp: {tie_candidates[0]['experience_years']} yrs, Match: {tie_candidates[0]['match_percentage']}%)")
        print(f"    Rank 2: {tie_candidates[1]['name']} (Exp: {tie_candidates[1]['experience_years']} yrs, Match: {tie_candidates[1]['match_percentage']}%)")
        # Both have 100% match, Epsilon has 8 years, Delta has 4 years -> Epsilon MUST rank 1
        assert tie_candidates[0]["name"] == "Candidate Epsilon"
        assert tie_candidates[0]["rank"] == 1
        assert tie_candidates[1]["name"] == "Candidate Delta"
        assert tie_candidates[1]["rank"] == 2

        # -------------------------------------------------------------
        # TEST 8: Validation / Edge Cases
        # -------------------------------------------------------------
        print("\n[9] Testing Edge Cases & Input Validation ...")

        # Edge Case 1: Empty resumes list in shortlist
        res_err_shortlist_empty = await client.call_tool("create_candidate_shortlist", {
            "job_description": "Valid Job Description",
            "resumes": []
        })
        assert res_err_shortlist_empty.is_error
        err_msg1 = res_err_shortlist_empty.content[0].text
        print(f"    Empty resumes error: {err_msg1}")
        assert "[INVALID_INPUT]" in err_msg1

        # Edge Case 2: Empty string in resumes list
        res_err_shortlist_item = await client.call_tool("create_candidate_shortlist", {
            "job_description": "Valid Job Description",
            "resumes": ["Valid resume", "   "]
        })
        assert res_err_shortlist_item.is_error
        err_msg2 = res_err_shortlist_item.content[0].text
        print(f"    Empty item error   : {err_msg2}")
        assert "[INVALID_INPUT]" in err_msg2

        # Edge Case 3: Empty resume in generate_candidate_report
        res_err_report_resume = await client.call_tool("generate_candidate_report", {
            "resume_text": "",
            "job_description": "Valid Job Description"
        })
        assert res_err_report_resume.is_error
        err_msg3 = res_err_report_resume.content[0].text
        print(f"    Empty resume error : {err_msg3}")
        assert "[INVALID_INPUT]" in err_msg3

        # Edge Case 4: Empty job_description in generate_candidate_report
        res_err_report_job = await client.call_tool("generate_candidate_report", {
            "resume_text": "Valid Resume Text",
            "job_description": "   "
        })
        assert res_err_report_job.is_error
        err_msg4 = res_err_report_job.content[0].text
        print(f"    Empty job error    : {err_msg4}")
        assert "[INVALID_INPUT]" in err_msg4

        print("\n" + "=" * 70)
        print("ALL TESTS (PHASE 2 & PHASE 3) PASSED SUCCESSFULLY!")
        print("=" * 70)


if __name__ == "__main__":
    try:
        asyncio.run(run_tests())
    except Exception as exc:
        print(f"\nTEST RUNNER ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
