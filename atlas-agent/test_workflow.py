import asyncio

from mcp_client.router import MCPRouter
from workflow.engine import WorkflowEngine


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

    print("=" * 70)
    print("WORKFLOW ENGINE TEST")
    print("=" * 70)

    try:
        print("\nConnecting to MCP servers...")

        await router.connect()

        print("MCP Router connected.")

        tools = await router.discover_tools()

        print("\nDiscovered tools:")
        print(tools)

        engine = WorkflowEngine(router)

        print("\nRunning workflow:")
        print(
            "100 km -> miles -> meters"
        )

        result = await engine.run_unit_conversion_chain(
            value=100,
            from_unit="km",
            intermediate_unit="miles",
            to_unit="meters",
        )

        print("\n" + "-" * 70)
        print("WORKFLOW RESULT")
        print("-" * 70)

        print(f"\nWorkflow: {result.workflow_name}")
        print(f"Status: {result.status}")

        for step in result.steps:
            print(f"\nStep: {step.step_name}")
            print(f"Tool: {step.tool_name}")
            print(f"Status: {step.status}")
            print(f"Result: {step.result}")

        print(f"\nFinal output: {result.output}")

        if result.status != "success":
            raise RuntimeError(
                f"Workflow failed: {result.error}"
            )

        final_value = float(
            result.output["result"]
        )

        if abs(final_value - 100000) > 0.001:
            raise AssertionError(
                f"Expected approximately 100000, "
                f"got {final_value}"
            )

        print("\n" + "=" * 70)
        print("WORKFLOW TEST PASSED SUCCESSFULLY!")
        print("=" * 70)

    finally:
        await router.close()
        print("\nMCP connections closed.")


if __name__ == "__main__":
    asyncio.run(main())