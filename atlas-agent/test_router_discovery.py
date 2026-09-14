import asyncio

from mcp_client.router import MCPRouter


ALGEBRA_PYTHON = r"..\algebra-mcp\.venv\Scripts\python.exe"
ALGEBRA_SERVER = r"..\algebra-mcp\algebra_server.py"

DATETIME_PYTHON = r"..\datetime-unit-mcp\.venv\Scripts\python.exe"
DATETIME_SERVER = r"..\datetime-unit-mcp\datetime_unit_server.py"


async def main():
    router = MCPRouter(
        algebra_command=ALGEBRA_PYTHON,
        algebra_script=ALGEBRA_SERVER,
        datetime_command=DATETIME_PYTHON,
        datetime_script=DATETIME_SERVER,
    )

    try:
        print("Connecting to MCP servers...")
        await router.connect()

        print("Connected.")
        print("Discovering tools...")

        tools = await router.discover_tools()

        print("\n" + "=" * 70)
        print("DISCOVERED TOOLS")
        print("=" * 70)

        for server, tool_list in tools.items():
            print(f"\n{server}:")
            for tool in tool_list:
                print(f"  - {tool}")

    finally:
        await router.close()


if __name__ == "__main__":
    asyncio.run(main())