"""Configuration settings for Talent Intelligence services."""

import os

RESUME_SERVICE_URL: str = os.getenv("RESUME_SERVICE_URL", "http://localhost:8001")
JOB_SERVICE_URL: str = os.getenv("JOB_SERVICE_URL", "http://localhost:8002")
MATCHING_SERVICE_URL: str = os.getenv("MATCHING_SERVICE_URL", "http://localhost:8003")
