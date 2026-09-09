"""Configuration for the Talent Intelligence MCP Gateway."""

import os


RESUME_SERVICE_URL = os.getenv(
    "RESUME_SERVICE_URL",
    "http://127.0.0.1:8001",
)

JOB_SERVICE_URL = os.getenv(
    "JOB_SERVICE_URL",
    "http://127.0.0.1:8002",
)

MATCHING_SERVICE_URL = os.getenv(
    "MATCHING_SERVICE_URL",
    "http://127.0.0.1:8003",
)

REQUEST_TIMEOUT = float(
    os.getenv(
        "REQUEST_TIMEOUT",
        "15",
    )
)


DEMO_API_KEYS = {
    "demo-client-key": {
        "client_id": "demo-client",
        "tenant_id": "tenant-demo",
        "allowed_tools": [
            "inspect_resume",
            "analyze_job",
            "compare_skills",
            "generate_candidate_report",
            "create_candidate_shortlist",
            "get_github_profile",
        ],
    },
    "readonly-client-key": {
        "client_id": "readonly-client",
        "tenant_id": "tenant-readonly",
        "allowed_tools": [
            "inspect_resume",
            "analyze_job",
            "compare_skills",
            "get_github_profile",
        ],
    },
}