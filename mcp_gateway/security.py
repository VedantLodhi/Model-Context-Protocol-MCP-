"""Lightweight authentication and authorization for the MCP Gateway."""

from dataclasses import dataclass

from mcp.server.mcpserver.exceptions import ToolError

from mcp_gateway.config import DEMO_API_KEYS


@dataclass(frozen=True)
class Principal:
    client_id: str
    tenant_id: str


def authenticate(api_key: str | None) -> Principal:
    """Authenticate a client using the demo API key."""

    if not api_key:
        raise ToolError(
            "[AUTHENTICATION_FAILED] Missing API key"
        )

    client = DEMO_API_KEYS.get(api_key)

    if client is None:
        raise ToolError(
            "[AUTHENTICATION_FAILED] Invalid API key"
        )

    return Principal(
        client_id=client["client_id"],
        tenant_id=client["tenant_id"],
    )


def authorize(
    api_key: str | None,
    tool_name: str,
) -> Principal:
    """Authenticate the client and verify tool access."""

    principal = authenticate(api_key)

    client = DEMO_API_KEYS[api_key]

    if tool_name not in client["allowed_tools"]:
        raise ToolError(
            f"[AUTHORIZATION_DENIED] Client "
            f"'{principal.client_id}' is not allowed to use "
            f"tool '{tool_name}'"
        )

    return principal