import asyncio

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


MCP_SERVERS = {
    "Resume MCP": r".\resume-mcp\resume_server.py",
    "Job MCP": r".\job-mcp\job_server.py",
    "Matching MCP": r".\matching-mcp\matching_server.py",
}


async def test_server(name: str, server_file: str):
    print(f"\n{'=' * 50}")
    print(f"{name}")
    print(f"{'=' * 50}")

    server_params = StdioServerParameters(
        command=r".\.venv\Scripts\python.exe",
        args=[server_file],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as client:

            await client.initialize()

            result = await client.list_tools()

            print("Discovered tools:")

            for tool in result.tools:
                print(f"  - {tool.name}")

            assert len(result.tools) > 0

            print("Tool discovery PASSED.")


async def main():
    print("TALENT INTELLIGENCE - 3 MCP INTEGRATION TEST")

    for name, server_file in MCP_SERVERS.items():
        await test_server(name, server_file)

    print("\n" + "=" * 50)
    print("ALL 3 MCP SERVERS PASSED SUCCESSFULLY!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())