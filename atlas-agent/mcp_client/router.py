from contextlib import AsyncExitStack

from atlas.models import RouteResult

from .arguments import ToolArgumentBuilder
from .capabilities import get_capabilities
from .client import MCPConnection
from .intent import detect_intent


class MCPRouter:
    """
    Routes user requests to the appropriate MCP capability.

    Responsibilities:
    - Maintain MCP server connections
    - Discover available tools
    - Detect request intent
    - Select the correct capability
    - Select the correct MCP server
    - Prepare tool arguments
    - Invoke the selected MCP tool

    The router does not perform business calculations.
    """

    def __init__(
        self,
        algebra_command: str,
        algebra_script: str,
        datetime_command: str,
        datetime_script: str,
    ):
        self.algebra = MCPConnection(
            name="Algebra",
            command=algebra_command,
            server_script=algebra_script,
        )

        self.datetime_unit = MCPConnection(
            name="DateTime/Unit",
            command=datetime_command,
            server_script=datetime_script,
        )

        self._stack: AsyncExitStack | None = None

        # Capability registry is the source of truth
        # for Atlas routing.
        self.capabilities = get_capabilities()

        # Map logical server names from the capability registry
        # to their actual MCP connections.
        self.connections = {
            "algebra": self.algebra,
            "datetime_unit": self.datetime_unit,
        }

        # Map MCP tool names to argument builders.
        # These builders only prepare arguments.
        self.argument_builders = {
            "solve_algebra": ToolArgumentBuilder.algebra,
            "convert_units": ToolArgumentBuilder.unit,
            "date_time": ToolArgumentBuilder.datetime,
        }

    async def connect(self) -> None:
        """
        Connect to all configured MCP servers.
        """

        self._stack = AsyncExitStack()
        await self._stack.__aenter__()

        await self.algebra.connect(self._stack)
        await self.datetime_unit.connect(self._stack)

    async def close(self) -> None:
        """
        Close all MCP connections.
        """

        if self._stack is not None:
            await self._stack.aclose()
            self._stack = None

    async def discover_tools(self) -> dict[str, list[str]]:
        """
        Discover tools from connected MCP servers.

        Also verifies that every registered capability
        actually exists on an MCP server.
        """

        algebra_tools = await self.algebra.list_tools()
        datetime_tools = await self.datetime_unit.list_tools()

        discovered = {
            "algebra": [
                tool.name
                for tool in algebra_tools.tools
            ],
            "datetime_unit": [
                tool.name
                for tool in datetime_tools.tools
            ],
        }

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

    async def route(self, query: str) -> RouteResult:
        """
        Route a natural-language query to an MCP capability.
        """

        intent = detect_intent(query)

        capability = self._find_capability(intent)

        if capability is None:
            return RouteResult(
                intent="unknown",
                tool_name=None,
                error=(
                    "I could not determine which MCP should "
                    "handle this request."
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
                    f"No MCP connection is configured for "
                    f"server '{capability.server}'."
                ),
            )

        argument_builder = self.argument_builders.get(
            capability.tool_name
        )

        if argument_builder is None:
            return RouteResult(
                intent=intent,
                tool_name=capability.tool_name,
                error=(
                    f"No argument builder is configured for "
                    f"tool '{capability.tool_name}'."
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

    def _find_capability(self, intent: str):
        """
        Find the capability registered for an intent.
        """

        for capability in self.capabilities:
            if capability.intent == intent:
                return capability

        return None