import asyncio
import json
import os

import httpx
from dotenv import load_dotenv

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client


load_dotenv()

TOKEN_URL = "https://mcp.rchilli.ai/token"
MCP_URL = "https://mcp.rchilli.ai/mcp"


async def get_access_token() -> str:
    client_id = os.getenv("RCHILLI_CLIENT_ID")
    client_secret = os.getenv("RCHILLI_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError(
            "RChilli credentials are missing from .env"
        )

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            TOKEN_URL,
            json={
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )

        response.raise_for_status()

        return response.json()["access_token"]


async def main():
    print("=" * 70)
    print("RCHILLI PARSE JOB DESCRIPTION TEST")
    print("=" * 70)

    token = await get_access_token()

    headers = {
        "Authorization": f"Bearer {token}",
    }

    job_description = """
    Senior Python Developer

    We are looking for a Senior Python Developer with strong
    backend development experience.

    Required Skills:
    Python
    FastAPI
    SQL
    Docker
    Kubernetes
    AWS

    Minimum Experience:
    5 years
    """

    async with httpx.AsyncClient(
        headers=headers,
        timeout=60.0,
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

                print("\nCalling RChilli tool:")
                print("parse_job_description")

                result = await session.call_tool(
                    "parse_job_description",
                    {
                        "jd_text": job_description,
                    },
                )

                print("\n" + "=" * 70)
                print("RCHILLI JD RESPONSE")
                print("=" * 70)

                print("\nIs Error:", result.is_error)

                print("\nStructured Content:")

                print(
                    json.dumps(
                        result.structured_content,
                        indent=2,
                        default=str,
                    )
                )


if __name__ == "__main__":
    asyncio.run(main())