import asyncio

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


async def main():
    server_params = StdioServerParameters(
        command=r".\.venv\Scripts\python.exe",
        args=[r".\resume-mcp\resume_server.py"],
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
            print("RESUME MCP - END-TO-END TEST")
            print("=" * 70)

            # ---------------------------------------------------------
            # 2. Tool discovery
            # ---------------------------------------------------------
            tools = await client.list_tools()

            print("\nDiscovered tools:")

            for tool in tools.tools:
                print(f"  - {tool.name}")

            tool_names = [tool.name for tool in tools.tools]

            assert "inspect_resume" in tool_names, (
                "inspect_resume tool was not discovered"
            )

            print("\nTool discovery PASSED.")

            # ---------------------------------------------------------
            # 3. Resume inspection
            # ---------------------------------------------------------
            print("\n" + "-" * 70)
            print("TEST 1 - RESUME INSPECTION")
            print("-" * 70)

            resume_text = """
            Vedant Lodhi
            Software Engineer

            Skills:
            Python, FastAPI, MCP, REST APIs, SQL

            Experience:
            2 years of experience in backend development.

            Education:
            Bachelor of Technology
            """

            result = await client.call_tool(
                "inspect_resume",
                {
                    "resume_text": resume_text,
                },
            )

            print(f"Resume input:\n{resume_text}")
            print(f"\nResult:\n{result}")

            assert result.is_error is False
            assert result.structured_content is not None

            print("Resume inspection PASSED.")

            # ---------------------------------------------------------
            # 4. Empty input validation
            # ---------------------------------------------------------
            print("\n" + "-" * 70)
            print("TEST 2 - INPUT VALIDATION")
            print("-" * 70)

            result = await client.call_tool(
                "inspect_resume",
                {
                    "resume_text": "",
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
            print("ALL RESUME MCP TESTS PASSED SUCCESSFULLY!")
            print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())