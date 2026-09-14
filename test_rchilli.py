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
        print("=" * 70)
        print("RCHILLI MCP TEST")
        print("=" * 70)

        await router.connect()

        print("\n[OK] All MCP connections established.")

        tools = await router.discover_tools()

        print("\n[OK] RChilli MCP connected.")
        print("\nRCHILLI TOOLS:")
        print("-" * 50)

        for tool in tools["rchilli"]:
            print(f"  - {tool}")

        print("\n[OK] RChilli tool discovery successful.")

    except Exception as exc:
        print("\n[ERROR] RChilli connection/discovery failed:")
        print(exc)

    finally:
        await router.close()


if __name__ == "__main__":
    asyncio.run(main())