from contextlib import AsyncExitStack
from typing import Any

from mcp.client.session import ClientSession
from mcp.client.stdio import (
    StdioServerParameters,
    stdio_client,
)


class MCPConnection:
    """
    Low-level MCP client connection.

    Responsible only for:
    - connecting to an MCP server
    - initializing the MCP session
    - discovering tools
    - invoking tools
    """

    def __init__(
        self,
        name: str,
        command: str,
        server_script: str,
    ):
        self.name = name
        self.command = command
        self.server_script = server_script
        self.session: ClientSession | None = None

    async def connect(
        self,
        stack: AsyncExitStack,
    ) -> None:
        server_params = StdioServerParameters(
            command=self.command,
            args=[self.server_script],
        )

        read_stream, write_stream = (
            await stack.enter_async_context(
                stdio_client(server_params)
            )
        )

        self.session = await stack.enter_async_context(
            ClientSession(
                read_stream,
                write_stream,
            )
        )

        await self.session.initialize()

    async def list_tools(self):
        if self.session is None:
            raise RuntimeError(
                f"{self.name} MCP is not connected."
            )

        return await self.session.list_tools()

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ):
        if self.session is None:
            raise RuntimeError(
                f"{self.name} MCP is not connected."
            )

        return await self.session.call_tool(
            tool_name,
            arguments,
        )