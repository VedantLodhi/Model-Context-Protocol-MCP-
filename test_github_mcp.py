import asyncio
import httpx

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client


SERVER_URL = "http://127.0.0.1:8000/mcp"


async def main():
    print("=" * 70)
    print("GITHUB MCP TOOL - END-TO-END TEST")
    print("=" * 70)

    async with httpx.AsyncClient(
        headers={
            "X-API-Key": "demo-client-key",
        },
        timeout=30.0,
    ) as http_client:

        async with streamable_http_client(
            SERVER_URL,
            http_client=http_client,
        ) as (read_stream, write_stream):

            async with ClientSession(
                read_stream,
                write_stream,
            ) as client:

                await client.initialize()

                print("\nMCP session initialized.")

                result = await client.call_tool(
                    "get_github_profile",
                    {
                        "username": "VedantLodhi",
                    },
                )

                print("\nGitHub MCP tool executed successfully.")

                print("\nResult:")
                print(result)


if __name__ == "__main__":
    asyncio.run(main())