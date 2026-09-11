import asyncio
import httpx

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client


SERVER_URL = "http://127.0.0.1:8020/mcp"


async def main():
    print("TALENT INTELLIGENCE HTTP MCP - END-TO-END TEST")
    print()

    async with httpx.AsyncClient(timeout=30.0) as http_client:

        async with streamable_http_client(
            SERVER_URL,
            http_client=http_client,
        ) as (read_stream, write_stream):

            async with ClientSession(
                read_stream,
                write_stream,
            ) as client:

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
                print("Central HTTP MCP tool discovery PASSED.")
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

                print("inspect_resume routing PASSED.")
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

                print("analyze_job routing PASSED.")
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

                print("compare_skills routing PASSED.")
                print(matching_result.structured_content)
                print()

                print("=" * 65)
                print(
                    "ALL CENTRAL HTTP MCP TESTS PASSED SUCCESSFULLY!"
                )
                print("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())