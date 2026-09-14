import asyncio
import os
import httpx

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client

TOKEN_URL = "https://mcp.rchilli.ai/token"
MCP_URL = "https://mcp.rchilli.ai/mcp"


async def main():

    client_id = os.getenv("RCHILLI_CLIENT_ID")
    client_secret = os.getenv("RCHILLI_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError(
            "RCHILLI_CLIENT_ID / RCHILLI_CLIENT_SECRET missing"
        )

    print("Requesting RChilli access token...")

    async with httpx.AsyncClient(timeout=30.0) as http_client:

        response = await http_client.post(
            TOKEN_URL,
            json={
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )

        response.raise_for_status()

        token = response.json()["access_token"]

    print("Token received.")
    print("Connecting to RChilli MCP...")

    headers = {
        "Authorization": f"Bearer {token}"
    }

    async with httpx.AsyncClient(
        headers=headers,
        timeout=30.0,
    ) as http_client:

        async with streamable_http_client(
            MCP_URL,
            http_client=http_client,
        ) as (read_stream, write_stream):

            async with ClientSession(
                read_stream,
                write_stream,
            ) as session:

                await session.initialize()

                print("RChilli MCP connected.")
                print("Calling parse_resume...\n")

                result = await session.call_tool(
                    "parse_resume",
                    {
                        "resume_text": """
Vedant Lodhi
Python Developer

Skills:
Python
SQL
FastAPI
Docker

Experience:
2 years experience as Python Developer

Education:
Bachelor of Technology
"""
                    },
                )

                print("=" * 70)
                print("RAW RCHILLI RESULT")
                print("=" * 70)

                print(result)

                print("\n" + "=" * 70)
                print("CONTENT")
                print("=" * 70)

                for item in result.content:
                    print("\nITEM TYPE:", type(item))
                    print("ITEM:", item)

                print("\n" + "=" * 70)
                print("STRUCTURED CONTENT")
                print("=" * 70)

                print(getattr(result, "structured_content", None))


if __name__ == "__main__":
    asyncio.run(main())
