"""Configuration for Talent Intelligence MCP Gateway."""

import os

RESUME_SERVICE_URL: str = os.getenv("RESUME_SERVICE_URL", "http://localhost:8001")
JOB_SERVICE_URL: str = os.getenv("JOB_SERVICE_URL", "http://localhost:8002")
MATCHING_SERVICE_URL: str = os.getenv("MATCHING_SERVICE_URL", "http://localhost:8003")

GATEWAY_HOST: str = os.getenv("GATEWAY_HOST", "127.0.0.1")
GATEWAY_PORT: int = int(os.getenv("GATEWAY_PORT", "8000"))
REQUEST_TIMEOUT: float = float(os.getenv("REQUEST_TIMEOUT", "10.0"))
