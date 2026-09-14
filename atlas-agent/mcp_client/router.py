from contextlib import AsyncExitStack
from typing import Any
import os
from dotenv import load_dotenv

load_dotenv()

import httpx

from mcp.client.session import ClientSession
from mcp.client.stdio import (
    StdioServerParameters,
    stdio_client,
)
from mcp.client.streamable_http import streamable_http_client

from atlas.models import RouteResult

from .arguments import ToolArgumentBuilder
from .capabilities import get_capabilities
from .client import MCPConnection
from .intent import detect_intent


class HTTPMCPConnection:
    """
    MCP connection for a Streamable HTTP MCP server.

    Used for Talent Intelligence MCP.
    """

    def __init__(
        self,
        name: str,
        server_url: str,
    ):
        self.name = name
        self.server_url = server_url
        self.http_client: httpx.AsyncClient | None = None
        self.http_context = None
        self.session: ClientSession | None = None

    async def connect(self) -> None:
        self.http_client = httpx.AsyncClient(
            timeout=30.0
        )

        self.http_context = streamable_http_client(
            self.server_url,
            http_client=self.http_client,
        )

        read_stream, write_stream = (
            await self.http_context.__aenter__()
        )

        self.session = ClientSession(
            read_stream,
            write_stream,
        )

        await self.session.__aenter__()
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

    async def close(self) -> None:
        if self.session is not None:
            await self.session.__aexit__(
                None,
                None,
                None,
            )
            self.session = None

        if self.http_context is not None:
            await self.http_context.__aexit__(
                None,
                None,
                None,
            )
            self.http_context = None

        if self.http_client is not None:
            await self.http_client.aclose()
            self.http_client = None


class RChilliMCPConnection:
    """
    MCP connection for the external RChilli MCP server.

    Authentication flow:

        Client ID + Client Secret
                ↓
        RChilli Token Endpoint
                ↓
        Access Token
                ↓
        RChilli MCP
                ↓
        Streamable HTTP MCP Session
    """

    def __init__(
        self,
        token_url: str,
        server_url: str,
    ):
        self.token_url = token_url
        self.server_url = server_url

        self.session: ClientSession | None = None

    async def connect(
        self,
        stack: AsyncExitStack,
    ) -> None:
        client_id = os.getenv("RCHILLI_CLIENT_ID")
        client_secret = os.getenv("RCHILLI_CLIENT_SECRET")

        if not client_id or not client_secret:
            raise RuntimeError(
                "RCHILLI_CLIENT_ID and "
                "RCHILLI_CLIENT_SECRET "
                "environment variables are required."
            )

        # ---------------------------------------------------------
        # Step 1: Request RChilli access token
        # ---------------------------------------------------------

        async with httpx.AsyncClient(
            timeout=30.0
        ) as token_client:

            response = await token_client.post(
                self.token_url,
                json={
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
            )

            if response.status_code != 200:
                raise RuntimeError(
                    "RChilli token request failed: "
                    f"HTTP {response.status_code} - "
                    f"{response.text}"
                )

            data = response.json()

            access_token = data.get(
                "access_token"
            )

            if not access_token:
                raise RuntimeError(
                    "RChilli token response did not "
                    "contain an access_token."
                )

        # ---------------------------------------------------------
        # Step 2: Create authenticated HTTP client
        # ---------------------------------------------------------

        http_client = await stack.enter_async_context(
            httpx.AsyncClient(
                headers={
                    "Authorization": (
                        f"Bearer {access_token}"
                    ),
                },
                timeout=30.0,
            )
        )

        # ---------------------------------------------------------
        # Step 3: Connect to RChilli Streamable HTTP MCP
        # ---------------------------------------------------------

        http_context = streamable_http_client(
            self.server_url,
            http_client=http_client,
        )

        read_stream, write_stream = (
            await stack.enter_async_context(
                http_context
            )
        )

        # ---------------------------------------------------------
        # Step 4: Create MCP session
        # ---------------------------------------------------------

        self.session = await stack.enter_async_context(
            ClientSession(
                read_stream,
                write_stream,
            )
        )

        # ---------------------------------------------------------
        # Step 5: Initialize MCP session
        # ---------------------------------------------------------

        await self.session.initialize()

    async def list_tools(self):
        if self.session is None:
            raise RuntimeError(
                "RChilli MCP is not connected."
            )

        return await self.session.list_tools()

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ):
        if self.session is None:
            raise RuntimeError(
                "RChilli MCP is not connected."
            )

        return await self.session.call_tool(
            tool_name,
            arguments,
        )


class MCPRouter:
    """
    Routes user requests to the appropriate MCP capability.

    Existing:
        Algebra MCP       -> stdio
        DateTime/Unit MCP -> stdio
        Talent MCP        -> Streamable HTTP

    New:
        RChilli MCP       -> Streamable HTTP
                             + Client Credentials authentication
    """

    def __init__(
        self,
        algebra_command: str,
        algebra_script: str,
        datetime_command: str,
        datetime_script: str,
    ):
        # ---------------------------------------------------------
        # Existing Algebra MCP
        # ---------------------------------------------------------

        self.algebra = MCPConnection(
            name="Algebra",
            command=algebra_command,
            server_script=algebra_script,
        )

        # ---------------------------------------------------------
        # Existing DateTime/Unit MCP
        # ---------------------------------------------------------

        self.datetime_unit = MCPConnection(
            name="DateTime/Unit",
            command=datetime_command,
            server_script=datetime_script,
        )

        # ---------------------------------------------------------
        # Existing Talent Intelligence MCP
        # ---------------------------------------------------------

        self.talent = HTTPMCPConnection(
            name="Talent Intelligence",
            server_url="http://127.0.0.1:8020/mcp",
        )

        # ---------------------------------------------------------
        # New RChilli MCP
        # ---------------------------------------------------------

        self.rchilli = RChilliMCPConnection(
            token_url="https://mcp.rchilli.ai/token",
            server_url="https://mcp.rchilli.ai/mcp",
        )

        self._stack: AsyncExitStack | None = None

        # ---------------------------------------------------------
        # Capability registry
        # ---------------------------------------------------------

        self.capabilities = get_capabilities()

        # ---------------------------------------------------------
        # MCP connections
        # ---------------------------------------------------------

        self.connections = {
            "algebra": self.algebra,
            "datetime_unit": self.datetime_unit,
            "talent": self.talent,
            "rchilli": self.rchilli,
        }

        # ---------------------------------------------------------
        # Argument builders
        # ---------------------------------------------------------

        self.argument_builders = {
            "solve_algebra": ToolArgumentBuilder.algebra,
            "convert_units": ToolArgumentBuilder.unit,
            "date_time": ToolArgumentBuilder.datetime,
        }

    async def connect(self) -> None:
        """
        Connect to all configured MCP servers.

        Algebra and DateTime/Unit remain stdio.

        Talent Intelligence uses local Streamable HTTP.

        RChilli uses external Streamable HTTP with
        Client Credentials authentication.
        """

        self._stack = AsyncExitStack()

        await self._stack.__aenter__()

        # ---------------------------------------------------------
        # Algebra
        # ---------------------------------------------------------

        await self.algebra.connect(
            self._stack
        )

        # ---------------------------------------------------------
        # DateTime/Unit
        # ---------------------------------------------------------

        await self.datetime_unit.connect(
            self._stack
        )

        # ---------------------------------------------------------
        # Local Talent MCP
        # ---------------------------------------------------------

        await self.talent.connect()

        # ---------------------------------------------------------
        # RChilli MCP
        # ---------------------------------------------------------

        await self.rchilli.connect(
            self._stack
        )

    async def close(self) -> None:
        """
        Close all MCP connections.
        """

        # Local Talent HTTP connection
        await self.talent.close()

        # RChilli, Algebra and DateTime resources
        # are managed by the AsyncExitStack.
        if self._stack is not None:
            await self._stack.aclose()
            self._stack = None

    async def discover_tools(
        self,
    ) -> dict[str, list[str]]:
        """
        Discover tools from all connected MCP servers.
        """

        # ---------------------------------------------------------
        # Algebra tools
        # ---------------------------------------------------------

        algebra_tools = (
            await self.algebra.list_tools()
        )

        # ---------------------------------------------------------
        # DateTime/Unit tools
        # ---------------------------------------------------------

        datetime_tools = (
            await self.datetime_unit.list_tools()
        )

        # ---------------------------------------------------------
        # Local Talent tools
        # ---------------------------------------------------------

        talent_tools = (
            await self.talent.list_tools()
        )

        # ---------------------------------------------------------
        # RChilli tools
        # ---------------------------------------------------------

        rchilli_tools = (
            await self.rchilli.list_tools()
        )

        # ---------------------------------------------------------
        # Build discovered tool registry
        # ---------------------------------------------------------

        discovered = {
            "algebra": [
                tool.name
                for tool in algebra_tools.tools
            ],
            "datetime_unit": [
                tool.name
                for tool in datetime_tools.tools
            ],
            "talent": [
                tool.name
                for tool in talent_tools.tools
            ],
            "rchilli": [
                tool.name
                for tool in rchilli_tools.tools
            ],
        }

        # ---------------------------------------------------------
        # Validate existing capability registry
        #
        # IMPORTANT:
        # RChilli tools are discovered here but are not yet
        # required to exist in the local capability registry.
        #
        # We will add RChilli workflow capabilities separately
        # after discovery is confirmed.
        # ---------------------------------------------------------

        discovered_tool_names = {
            tool_name
            for tool_names in discovered.values()
            for tool_name in tool_names
        }

        for capability in self.capabilities:
            if capability.tool_name not in discovered_tool_names:
                raise RuntimeError(
                    f"Capability registry expects tool "
                    f"'{capability.tool_name}', but that tool "
                    f"was not discovered from an MCP server."
                )

        return discovered

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict,
    ):
        """
        Execute an MCP tool with explicit arguments.
        """

        capability = None

        for item in self.capabilities:
            if item.tool_name == tool_name:
                capability = item
                break

        if capability is None:
            raise RuntimeError(
                f"Unknown MCP tool: {tool_name}"
            )

        connection = self.connections.get(
            capability.server
        )

        if connection is None:
            raise RuntimeError(
                f"No MCP connection configured for "
                f"server '{capability.server}'."
            )

        return await connection.call_tool(
            tool_name,
            arguments,
        )

    async def route(
        self,
        query: str,
    ) -> RouteResult:
        """
        Route a natural-language query to an MCP capability.
        """

        intent = detect_intent(query)

        capability = self._find_capability(
            intent
        )

        if capability is None:
            return RouteResult(
                intent="unknown",
                tool_name=None,
                error=(
                    "I could not determine which MCP "
                    "should handle this request."
                ),
            )

        connection = self.connections.get(
            capability.server
        )

        if connection is None:
            return RouteResult(
                intent=intent,
                tool_name=capability.tool_name,
                error=(
                    f"No MCP connection is configured "
                    f"for server '{capability.server}'."
                ),
            )

        argument_builder = (
            self.argument_builders.get(
                capability.tool_name
            )
        )

        if argument_builder is None:
            return RouteResult(
                intent=intent,
                tool_name=capability.tool_name,
                error=(
                    f"No argument builder is configured "
                    f"for tool '{capability.tool_name}'."
                ),
            )

        try:
            arguments = argument_builder(query)

        except Exception as exc:
            return RouteResult(
                intent=intent,
                tool_name=capability.tool_name,
                error=(
                    f"Could not prepare arguments for "
                    f"'{capability.tool_name}': {exc}"
                ),
            )

        try:
            result = await connection.call_tool(
                capability.tool_name,
                arguments,
            )

        except Exception as exc:
            return RouteResult(
                intent=intent,
                tool_name=capability.tool_name,
                error=(
                    f"Unable to execute MCP tool "
                    f"'{capability.tool_name}': {exc}"
                ),
            )

        return RouteResult(
            intent=intent,
            tool_name=capability.tool_name,
            data=result,
        )

    def _find_capability(
        self,
        intent: str,
    ):
        """
        Find the capability registered for an intent.
        """

        for capability in self.capabilities:
            if capability.intent == intent:
                return capability

        return None
