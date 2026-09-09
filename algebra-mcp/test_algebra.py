import asyncio

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


async def main():
    server_params = StdioServerParameters(
        command=r".\.venv\Scripts\python.exe",
        args=["algebra_server.py"],
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
            print("ALGEBRA MCP - END-TO-END TEST")
            print("=" * 70)

            # ---------------------------------------------------------
            # 2. Tool discovery
            # ---------------------------------------------------------
            tools = await client.list_tools()

            print("\nDiscovered tools:")

            for tool in tools.tools:
                print(f"  - {tool.name}")

            tool_names = [tool.name for tool in tools.tools]

            assert "solve_algebra" in tool_names, (
                "solve_algebra tool was not discovered"
            )

            print("\nTool discovery PASSED.")

            # ---------------------------------------------------------
            # 3. Linear equation
            # ---------------------------------------------------------
            print("\n" + "-" * 70)
            print("TEST 1 - LINEAR EQUATION")
            print("-" * 70)

            problem = "2x + 5 = 15"

            result = await client.call_tool(
                "solve_algebra",
                {
                    "problem": problem,
                },
            )

            print(f"Problem: {problem}")
            print(f"Result : {result}")

            assert result.is_error is False
            assert result.structured_content["solution"] == ["5"]

            print("Linear equation PASSED.")

            # ---------------------------------------------------------
            # 4. Quadratic equation
            # ---------------------------------------------------------
            print("\n" + "-" * 70)
            print("TEST 2 - QUADRATIC EQUATION")
            print("-" * 70)

            problem = "x^2 - 5x + 6 = 0"

            result = await client.call_tool(
                "solve_algebra",
                {
                    "problem": problem,
                },
            )

            print(f"Problem: {problem}")
            print(f"Result : {result}")

            assert result.is_error is False
            assert result.structured_content["solution"] == ["2", "3"]

            print("Quadratic equation PASSED.")

            # ---------------------------------------------------------
            # 5. Implicit multiplication
            # ---------------------------------------------------------
            print("\n" + "-" * 70)
            print("TEST 3 - IMPLICIT MULTIPLICATION")
            print("-" * 70)

            problem = "3x - 9 = 0"

            result = await client.call_tool(
                "solve_algebra",
                {
                    "problem": problem,
                },
            )

            print(f"Problem: {problem}")
            print(f"Result : {result}")

            assert result.is_error is False
            assert result.structured_content["solution"] == ["3"]

            print("Implicit multiplication PASSED.")

            # ---------------------------------------------------------
            # 6. Expression simplification
            # ---------------------------------------------------------
            print("\n" + "-" * 70)
            print("TEST 4 - EXPRESSION SIMPLIFICATION")
            print("-" * 70)

            problem = "2*x + 3*x"

            result = await client.call_tool(
                "solve_algebra",
                {
                    "problem": problem,
                },
            )

            print(f"Problem: {problem}")
            print(f"Result : {result}")

            assert result.is_error is False
            assert result.structured_content["solution"] == "5*x"

            print("Expression simplification PASSED.")

            # ---------------------------------------------------------
            # 7. Parentheses
            # ---------------------------------------------------------
            print("\n" + "-" * 70)
            print("TEST 5 - PARENTHESES")
            print("-" * 70)

            problem = "2(x + 3) = 14"

            result = await client.call_tool(
                "solve_algebra",
                {
                    "problem": problem,
                },
            )

            print(f"Problem: {problem}")
            print(f"Result : {result}")

            assert result.is_error is False
            assert result.structured_content["solution"] == ["4"]

            print("Parentheses handling PASSED.")

            # ---------------------------------------------------------
            # 8. Empty input
            # ---------------------------------------------------------
            print("\n" + "-" * 70)
            print("TEST 6 - INPUT VALIDATION")
            print("-" * 70)

            result = await client.call_tool(
                "solve_algebra",
                {
                    "problem": "",
                },
            )

            print("Empty input result:")
            print(result)

            assert result.is_error is True

            print("Empty input validation PASSED.")

            # ---------------------------------------------------------
            # 9. Invalid algebra
            # ---------------------------------------------------------
            print("\n" + "-" * 70)
            print("TEST 7 - INVALID ALGEBRA")
            print("-" * 70)

            problem = "this is not mathematics"

            result = await client.call_tool(
                "solve_algebra",
                {
                    "problem": problem,
                },
            )

            print(f"Problem: {problem}")
            print(f"Result : {result}")

            assert result.is_error is True

            print("Invalid algebra validation PASSED.")

            # ---------------------------------------------------------
            # Final result
            # ---------------------------------------------------------
            print("\n" + "=" * 70)
            print("ALL ALGEBRA MCP TESTS PASSED SUCCESSFULLY!")
            print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())