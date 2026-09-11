import asyncio

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


async def main():
    server_params = StdioServerParameters(
        command=r".\.venv\Scripts\python.exe",
        args=[r".\job-mcp\job_server.py"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(
            read_stream,
            write_stream,
        ) as client:

            # ---------------------------------------------------------
            # 1. Initialize MCP session
            # ---------------------------------------------------------
            await client.initialize()

            print("=" * 70)
            print("JOB MCP - END-TO-END TEST")
            print("=" * 70)

            # ---------------------------------------------------------
            # 2. Tool discovery
            # ---------------------------------------------------------
            tools = await client.list_tools()

            print("\nDiscovered tools:")

            for tool in tools.tools:
                print(f"  - {tool.name}")

            tool_names = [tool.name for tool in tools.tools]

            assert "analyze_job" in tool_names, (
                "analyze_job tool was not discovered"
            )

            print("\nTool discovery PASSED.")

            # ---------------------------------------------------------
            # 3. Job analysis
            # ---------------------------------------------------------
            print("\n" + "-" * 70)
            print("TEST 1 - JOB ANALYSIS")
            print("-" * 70)

            job_description = """
            Software Engineer

            We are looking for a Software Engineer with experience in
            Python, FastAPI, REST APIs and SQL.

            Requirements:
            - 2+ years of experience
            - Strong Python skills
            - Experience with FastAPI
            - Knowledge of REST APIs
            - SQL experience
            """

            result = await client.call_tool(
                "analyze_job",
                {
                    "job_description": job_description,
                },
            )

            print(f"Job description:\n{job_description}")
            print(f"\nResult:\n{result}")

            assert result.is_error is False
            assert result.structured_content is not None

            print("Job analysis PASSED.")

            # ---------------------------------------------------------
            # 4. Empty input validation
            # ---------------------------------------------------------
            print("\n" + "-" * 70)
            print("TEST 2 - INPUT VALIDATION")
            print("-" * 70)

            result = await client.call_tool(
                "analyze_job",
                {
                    "job_description": "",
                },
            )

            print("Empty input result:")
            print(result)

            assert result.is_error is True

            print("Empty input validation PASSED.")

            # ---------------------------------------------------------
            # Final result
            # ---------------------------------------------------------
            print("\n" + "=" * 70)
            print("ALL JOB MCP TESTS PASSED SUCCESSFULLY!")
            print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())