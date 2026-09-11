import asyncio

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def main():
    print("MATCHING MCP - END-TO-END TEST")
    print()

    server_params = StdioServerParameters(
        command=r".\.venv\Scripts\python.exe",
        args=[r".\matching-mcp\matching_server.py"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as client:

            await client.initialize()

            tools_result = await client.list_tools()

            print("Discovered tools:")
            for tool in tools_result.tools:
                print(f"  - {tool.name}")

            assert any(
                tool.name == "compare_skills"
                for tool in tools_result.tools
            )

            print()
            print("Tool discovery PASSED.")
            print()

            result = await client.call_tool(
                "compare_skills",
                {
                    "candidate_skills": [
                        "Python",
                        "FastAPI",
                        "SQL",
                    ],
                    "required_skills": [
                        "Python",
                        "FastAPI",
                        "SQL",
                    ],
                },
            )

            print("Matching result:")
            print(result)

            assert result.is_error is False
            assert result.structured_content is not None

            print()
            print("Skill matching PASSED.")
            print()

            invalid_result = await client.call_tool(
                "compare_skills",
                {
                    "candidate_skills": [],
                    "required_skills": [
                        "Python",
                    ],
                },
            )

            assert invalid_result.is_error is True

            print("Empty candidate validation PASSED.")
            print()

            invalid_result = await client.call_tool(
                "compare_skills",
                {
                    "candidate_skills": [
                        "Python",
                    ],
                    "required_skills": [],
                },
            )

            assert invalid_result.is_error is True

            print("Empty required skills validation PASSED.")
            print()

            print("ALL MATCHING MCP TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    asyncio.run(main())