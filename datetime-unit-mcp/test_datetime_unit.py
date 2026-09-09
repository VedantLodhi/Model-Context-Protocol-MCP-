import asyncio

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


async def main():
    server_params = StdioServerParameters(
        command=r".\.venv\Scripts\python.exe",
        args=["datetime_unit_server.py"],
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
            print("DATETIME / UNIT MCP - END-TO-END TEST")
            print("=" * 70)

            # ---------------------------------------------------------
            # 2. Tool discovery
            # ---------------------------------------------------------
            tools = await client.list_tools()

            print("\nDiscovered tools:")

            for tool in tools.tools:
                print(f"  - {tool.name}")

            tool_names = [tool.name for tool in tools.tools]

            assert "convert_units" in tool_names
            assert "date_time" in tool_names

            print("\nTool discovery PASSED.")

            # ---------------------------------------------------------
            # 3. Kilometers -> Miles
            # ---------------------------------------------------------
            print("\n" + "-" * 70)
            print("TEST 1 - KILOMETERS TO MILES")
            print("-" * 70)

            result = await client.call_tool(
                "convert_units",
                {
                    "value": 10,
                    "from_unit": "km",
                    "to_unit": "mile",
                },
            )

            print("10 km -> miles")
            print(f"Result: {result}")

            assert result.is_error is False
            assert abs(
                result.structured_content["result"] - 6.21371
            ) < 0.001

            print("Kilometers conversion PASSED.")

            # ---------------------------------------------------------
            # 4. Kilograms -> Pounds
            # ---------------------------------------------------------
            print("\n" + "-" * 70)
            print("TEST 2 - KILOGRAMS TO POUNDS")
            print("-" * 70)

            result = await client.call_tool(
                "convert_units",
                {
                    "value": 5,
                    "from_unit": "kg",
                    "to_unit": "pound",
                },
            )

            print("5 kg -> pounds")
            print(f"Result: {result}")

            assert result.is_error is False
            assert abs(
                result.structured_content["result"] - 11.0231
            ) < 0.001

            print("Kilograms conversion PASSED.")

            # ---------------------------------------------------------
            # 5. Celsius -> Fahrenheit
            # ---------------------------------------------------------
            print("\n" + "-" * 70)
            print("TEST 3 - CELSIUS TO FAHRENHEIT")
            print("-" * 70)

            result = await client.call_tool(
                "convert_units",
                {
                    "value": 100,
                    "from_unit": "degC",
                    "to_unit": "degF",
                },
            )

            print("100 Celsius -> Fahrenheit")
            print(f"Result: {result}")

            assert result.is_error is False
            assert abs(
                result.structured_content["result"] - 212
            ) < 0.001

            print("Temperature conversion PASSED.")

            # ---------------------------------------------------------
            # 6. Current Date/Time
            # ---------------------------------------------------------
            print("\n" + "-" * 70)
            print("TEST 4 - CURRENT DATE/TIME")
            print("-" * 70)

            result = await client.call_tool(
                "date_time",
                {
                    "operation": "now",
                    "timezone": "Asia/Kolkata",
                },
            )

            print("Current time in Asia/Kolkata")
            print(f"Result: {result}")

            assert result.is_error is False
            assert result.structured_content["timezone"] == "Asia/Kolkata"
            assert result.structured_content["datetime"]

            print("Current date/time PASSED.")

            # ---------------------------------------------------------
            # 7. Add days
            # ---------------------------------------------------------
            print("\n" + "-" * 70)
            print("TEST 5 - ADD DAYS")
            print("-" * 70)

            result = await client.call_tool(
                "date_time",
                {
                    "operation": "add_days",
                    "date": "2026-01-01T00:00:00",
                    "days": 10,
                },
            )

            print("2026-01-01 + 10 days")
            print(f"Result: {result}")

            assert result.is_error is False
            assert result.structured_content["result"].startswith(
                "2026-01-11"
            )

            print("Add days PASSED.")

            # ---------------------------------------------------------
            # 8. Date difference
            # ---------------------------------------------------------
            print("\n" + "-" * 70)
            print("TEST 6 - DATE DIFFERENCE")
            print("-" * 70)

            result = await client.call_tool(
                "date_time",
                {
                    "operation": "difference",
                    "date": (
                        "2026-01-01T00:00:00,"
                        "2026-01-15T00:00:00"
                    ),
                },
            )

            print("2026-01-01 -> 2026-01-15")
            print(f"Result: {result}")

            assert result.is_error is False
            assert result.structured_content["difference_days"] == 14

            print("Date difference PASSED.")

            # ---------------------------------------------------------
            # 9. Invalid input
            # ---------------------------------------------------------
            print("\n" + "-" * 70)
            print("TEST 7 - INVALID INPUT")
            print("-" * 70)

            result = await client.call_tool(
                "convert_units",
                {
                    "value": 10,
                    "from_unit": "invalid_unit",
                    "to_unit": "km",
                },
            )

            print("Invalid unit result:")
            print(result)

            assert result.is_error is True

            print("Invalid input validation PASSED.")

            # ---------------------------------------------------------
            # Final result
            # ---------------------------------------------------------
            print("\n" + "=" * 70)
            print("ALL DATETIME / UNIT MCP TESTS PASSED SUCCESSFULLY!")
            print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())