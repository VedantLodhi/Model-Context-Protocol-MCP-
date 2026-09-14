import asyncio

from atlas.host import AtlasHost
from mcp_client.router import MCPRouter


ALGEBRA_PYTHON = r"..\algebra-mcp\.venv\Scripts\python.exe"
ALGEBRA_SERVER = r"..\algebra-mcp\algebra_server.py"

DATETIME_PYTHON = r"..\datetime-unit-mcp\.venv\Scripts\python.exe"
DATETIME_SERVER = r"..\datetime-unit-mcp\datetime_unit_server.py"


async def main() -> None:
    print("=" * 70)
    print("ATLAS AGENT")
    print("=" * 70)

    router = MCPRouter(
        algebra_command=ALGEBRA_PYTHON,
        algebra_script=ALGEBRA_SERVER,
        datetime_command=DATETIME_PYTHON,
        datetime_script=DATETIME_SERVER,
    )

    print("\nStarting Atlas...")

    try:
        # Connect Atlas MCP Router to both MCP servers
        await router.connect()

        print("MCP Router connected.")
        print("Algebra MCP connected.")
        print("DateTime/Unit MCP connected.")

        # Discover tools from both MCP servers
        tools = await router.discover_tools()

        print("\nDiscovered MCP tools:")

        print("\nAlgebra MCP:")
        for tool in tools["algebra"]:
            print(f"  - {tool}")

        print("\nDateTime/Unit MCP:")
        for tool in tools["datetime_unit"]:
            print(f"  - {tool}")

        # Create the user-facing Atlas Host
        host = AtlasHost(router)

        print("\nAtlas is ready.")
        print("Type 'history' to view memory.")
        print("Type 'details' to view execution details.")
        print("Type 'clear' to clear memory.")
        print("Type 'exit' to stop.")

        while True:
            print("\nYou: ", end="", flush=True)

            lines = []

            while True:
                line = input()

                # Blank line = submit multiline query
                if not line.strip():
                    break

                lines.append(line)

            query = "\n".join(lines).strip()

            # Ignore empty input
            if not query:
                print("\nAtlas: Please enter a query.")
                continue

            # Exit Atlas
            if query.lower() == "exit":
                break

            # Show conversation history
            if query.lower() == "history":
                host.show_history()
                continue

            # Show structured MCP execution history
            if query.lower() == "details":
                host.show_execution_history()
                continue

            # Clear Atlas memory
            if query.lower() == "clear":
                host.clear_memory()
                print("\nAtlas memory cleared.")
                continue

            # Normal user request
            response = await host.handle_query(query)

            print(f"\nAtlas: {response}")

    finally:
        # Always close both MCP connections
        await router.close()

    print("\nAtlas stopped.")


if __name__ == "__main__":
    asyncio.run(main())