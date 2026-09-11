import asyncio

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def main():
    print("TALENT INTELLIGENCE MCP SERVER - END-TO-END TEST")
    print()

    server_params = StdioServerParameters(
        command=r".\.venv\Scripts\python.exe",
        args=[r".\talent-mcp-router\router.py"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as client:

            await client.initialize()

            tools_result = await client.list_tools()

            print("Discovered tools:")

            for tool in tools_result.tools:
                print(f"  - {tool.name}")

            tool_names = {
                tool.name
                for tool in tools_result.tools
            }

            assert "inspect_resume" in tool_names
            assert "analyze_job" in tool_names
            assert "compare_skills" in tool_names

            print()
            print("Central MCP tool discovery PASSED.")
            print()

            # Resume
            resume_result = await client.call_tool(
                "inspect_resume",
                {
                    "resume_text": (
                        "Vedant Lodhi\n"
                        "Python SQL FastAPI\n"
                        "2 years experience\n"
                        "Bachelor"
                    ),
                },
            )

            assert resume_result.is_error is False
            assert resume_result.structured_content is not None

            print("inspect_resume → Resume MCP → Resume API PASSED.")
            print(resume_result.structured_content)
            print()

            # Job
            job_result = await client.call_tool(
                "analyze_job",
                {
                    "job_description": (
                        "Software Engineer\n"
                        "Required skills: Python, SQL, FastAPI\n"
                        "2 years experience"
                    ),
                },
            )

            assert job_result.is_error is False
            assert job_result.structured_content is not None

            print("analyze_job → Job MCP → Job API PASSED.")
            print(job_result.structured_content)
            print()

            # Matching
            matching_result = await client.call_tool(
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
                    ],
                },
            )

            assert matching_result.is_error is False
            assert matching_result.structured_content is not None

            print(
                "compare_skills → Matching MCP → Matching API PASSED."
            )
            print(matching_result.structured_content)
            print()

            print("=" * 65)
            print(
                "ALL CENTRAL TALENT INTELLIGENCE MCP TESTS PASSED!"
            )
            print("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())