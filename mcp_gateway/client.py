"""Lightweight HTTP client helper for calling backend REST services."""

from typing import Any, Dict
import httpx
from mcp_gateway.config import REQUEST_TIMEOUT


class GatewayBackendError(Exception):
    """Clean domain exception for backend communication failures."""
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


async def call_backend(
    service_url: str,
    path: str,
    payload: Dict[str, Any],
    request_id: str
) -> Dict[str, Any]:
    """
    Call an internal backend REST service, propagating correlation ID and unwrapping data.
    
    Translates transport/HTTP/business errors into clean GatewayBackendError without leaking stack traces.
    """
    url = f"{service_url.rstrip('/')}/{path.lstrip('/')}"
    headers = {
        "Content-Type": "application/json",
        "X-Request-ID": request_id
    }

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(url, json=payload, headers=headers)
    except httpx.TimeoutException:
        raise GatewayBackendError(
            code="TIMEOUT",
            message=f"Request to backend service at {path} timed out after {REQUEST_TIMEOUT}s"
        )
    except httpx.RequestError as exc:
        raise GatewayBackendError(
            code="DEPENDENCY_FAILED",
            message=f"Unable to connect to backend service at {url}: {str(exc)}"
        )

    # Parse response JSON
    try:
        body = response.json()
    except Exception:
        raise GatewayBackendError(
            code="INTERNAL_ERROR",
            message=f"Backend service at {path} returned non-JSON response (HTTP {response.status_code})"
        )

    # Check for HTTP or logical errors
    if response.status_code != 200 or not body.get("success", True):
        error_info = body.get("error") or {}
        code = error_info.get("code") or ("INVALID_INPUT" if response.status_code == 422 else "INTERNAL_ERROR")
        message = error_info.get("message") or f"Backend request failed with status {response.status_code}"
        raise GatewayBackendError(code=code, message=message)

    # Return unwrapped structured data
    return body.get("data", {})
