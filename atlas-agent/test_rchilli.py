import asyncio
import os

import httpx
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client


TOKEN_URL = "https://mcp.rchilli.ai/token"
MCP_URL = "https://mcp.rchilli.ai/mcp"


async def get_access_token() -> str:
    client_id = os.getenv("RCHILLI_CLIENT_ID")
    client_secret = os.getenv("RCHILLI_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError(
            "RCHILLI_CLIENT_ID and RCHILLI_CLIENT_SECRET "
            "environment variables are required."
        )

    async with httpx.AsyncClient(timeout=30.0) as http_client:
        response = await http_client.post(
            TOKEN_URL,
            json={
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )

        response.raise_for_status()

        data = response.json()

        return data["access_token"]


async def main():
    print("=" * 70)
    print("RCHILLI MCP TEST")
    print("=" * 70)

    print("\nRequesting access token...")

    token = await get_access_token()

    print("Access token received.")

    headers = {
        "Authorization": f"Bearer {token}",
    }

    async with httpx.AsyncClient(
        headers=headers,
        timeout=30.0,
    ) as http_client:

        print("Connecting to RChilli MCP...")

        async with streamable_http_client(
            MCP_URL,
            http_client=http_client,
        ) as (read_stream, write_stream):

            async with ClientSession(
                read_stream,
                write_stream,
            ) as session:

                print("Initializing MCP session...")

                await session.initialize()

                print("RChilli MCP connected.")

                print("\nDiscovering tools...")

                result = await session.list_tools()

                print(f"\nFound {len(result.tools)} tools:\n")

                for tool in result.tools:
                    print(f"- {tool.name}")


if __name__ == "__main__":
    asyncio.run(main())