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

                print("RChilli MCP connected.")
                print("Calling score_resume_against_jd...\n")

                resume = """
Vedant Lodhi

Python Developer

Education:
Bachelor of Technology

Skills:
Python
FastAPI
SQL
Docker

Experience:
2 years of Python development experience.
Strong backend development experience.
"""

                job_description = """
Senior Python Developer

We are looking for a Python developer with 5 years of experience.

Required skills:
Python
FastAPI
SQL
Docker
Kubernetes
AWS
React
Java

The candidate should have strong backend development experience.
"""

                result = await session.call_tool(
                    "score_resume_against_jd",
                    {
                        "index_key": "",
                        "match_type": "JD to Resume",
                        "resume_content": resume,
                        "resume_file_name": "resume.txt",
                        "jd_content": job_description,
                        "jd_file_name": "job_description.txt",
                    },
                )

                print("=" * 70)
                print("RAW RESULT")
                print("=" * 70)
                print(result)

                print("\n" + "=" * 70)
                print("STRUCTURED CONTENT")
                print("=" * 70)
                print(getattr(result, "structured_content", None))

                print("\n" + "=" * 70)
                print("IS ERROR")
                print("=" * 70)
                print(getattr(result, "is_error", None))


if __name__ == "__main__":
    asyncio.run(main())