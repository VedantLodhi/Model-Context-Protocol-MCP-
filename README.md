# Talent Intelligence MCP Gateway (Backend Services & MCP Layer)

Welcome to the **Talent Intelligence MCP Gateway** learning project! This repository contains both the internal backend microservices and the **Model Context Protocol (MCP) Gateway** layer that exposes high-level agentic capabilities to AI clients and assistants.

---

## 1. Project Overview

The Talent Intelligence project demonstrates how an intelligent agent or client (e.g., Claude Desktop, MCP Inspector, or any AI assistant) can interact with diverse backend HR and talent systems using a single unified protocol: the **Model Context Protocol (MCP)**.

The system is organized into two distinct layers:
1. **Internal REST Microservices:** Dedicated backend services managing resumes, job specs, and candidate-job matching.
2. **MCP Gateway:** A protocol adapter and orchestrator running over **Streamable HTTP** that translates standard MCP protocol commands (`tools/list`, `tools/call`) into internal HTTP REST calls while maintaining end-to-end correlation tracing.

---

## 2. Why Three Separate Backend Services?

In modern software engineering and enterprise HR technology stacks, services are rarely monolithic. Different capabilities often live in separate systems:
- An **Applicant Tracking System (ATS)** or Resume Parsing engine handles CVs and profile ingestion.
- A **Job Requisition System** parses job descriptions and defines role requirements.
- A **Scoring / Matching Engine** compares candidates against job requirements.

By building three separate microservices:
1. We simulate a realistic multi-service enterprise environment.
2. We demonstrate the core value of an **MCP Gateway**: acting as a single, intelligent façade that hides service fragmentation, handles routing, and combines multi-service responses into high-level agentic tools.

---

## 3. Architecture Diagram

```text
                  MCP Client / Python MCP Client / Inspector
                                      |
                                      | JSON-RPC over Streamable HTTP (:8000/mcp)
                                      v
                     +----------------------------------+
                     |           MCP Gateway            |
                     |     (Talent Intelligence MCP)    |
                     |                                  |
                     | Discovery  : tools/list          |
                     | Execution  : tools/call          |
                     | Tracing    : X-Request-ID        |
                     |                                  |
                     | Exposed Semantic Tools (5):      |
                     |  [Atomic Tools]                  |
                     |   - inspect_resume               |
                     |   - analyze_job                  |
                     |   - compare_skills               |
                     |  [Composite Capabilities]        |
                     |   - generate_candidate_report    |
                     |   - create_candidate_shortlist   |
                     +----------------+-----------------+
                                      |
                                      | Internal HTTP REST (HTTPX)
                                      v
                 +--------------------+--------------------+
                 |                    |                    |
                 v                    v                    v
           Resume API             Job API             Matching API
             :8001                 :8002                 :8003
```

---

## 4. Installation Requirements

- **Operating System:** Windows 10/11, macOS, or Linux
- **Python:** Version 3.11 or newer (Python 3.12 verified)
- **Git:** Required for version control
- **Terminal:** PowerShell, Command Prompt, or Bash

---

## 5. Python Installation (Windows)

If Python is missing on Windows, install Python 3.12 via Windows Package Manager:

```powershell
winget install --id Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements
```

Verify installation:
```powershell
python --version
pip --version
```

---

## 6. Git Installation (Windows)

If Git is missing, install it via `winget`:

```powershell
winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements
```

Verify installation:
```powershell
git --version
```

---

## 7. Virtual Environment Setup

Always use a Python virtual environment to keep dependencies isolated:

```powershell
# Navigate to the project root
cd "d:\MCP Project\talent-intelligence-mcp"

# Create .venv
python -m venv .venv

# Activate the virtual environment on Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
```

---

## 8. Dependency Installation

With the virtual environment activated, install the required packages:

```powershell
pip install -r requirements.txt
```

Installed core packages:
- `fastapi` — High-performance modern web framework
- `uvicorn` — Lightning-fast ASGI web server
- `pydantic` — Data validation and parsing
- `httpx` — Async HTTP client for backend service communication
- `mcp[cli]` — Official Model Context Protocol Python SDK v2

---

## 9. How to Start All Services

Open four separate terminals (or run as background processes), activate `.venv`, and start each service:

### Terminal 1: Resume Service (Port 8001)
```powershell
.\.venv\Scripts\python.exe -m uvicorn services.resume_service.main:app --port 8001
```

### Terminal 2: Job Service (Port 8002)
```powershell
.\.venv\Scripts\python.exe -m uvicorn services.job_service.main:app --port 8002
```

### Terminal 3: Matching Service (Port 8003)
```powershell
.\.venv\Scripts\python.exe -m uvicorn services.matching_service.main:app --port 8003
```

### Terminal 4: MCP Gateway (Port 8000)
```powershell
.\.venv\Scripts\python.exe -m uvicorn mcp_gateway.server:app --host 127.0.0.1 --port 8000
```

---

## 10. Port & Endpoint Mapping

| Service Name | Port | Base URL / Protocol | Primary Endpoints |
|---|---|---|---|
| **Resume Service** | `8001` | HTTP REST | `GET /health`, `POST /inspect` |
| **Job Service** | `8002` | HTTP REST | `GET /health`, `POST /analyze` |
| **Matching Service** | `8003` | HTTP REST | `GET /health`, `POST /compare` |
| **MCP Gateway** | `8000` | Streamable HTTP (MCP) | `POST /mcp` (JSON-RPC) |

---

## 11. Backend Health Endpoints

Each backend service exposes a simple health probe returning HTTP 200:

- `GET http://localhost:8001/health`
- `GET http://localhost:8002/health`
- `GET http://localhost:8003/health`

---

## 12. Interactive Backend API Docs

- **Resume Service Docs:** [http://localhost:8001/docs](http://localhost:8001/docs)
- **Job Service Docs:** [http://localhost:8002/docs](http://localhost:8002/docs)
- **Matching Service Docs:** [http://localhost:8003/docs](http://localhost:8003/docs)

---

## 13. Phase 2 — Atomic MCP Capabilities

Atomic capabilities correspond 1-to-1 with a backend domain capability:

1. **`inspect_resume`**
   - **Description:** Inspect and parse raw candidate resume text into structured candidate profile data.
   - **Arguments:** `resume_text: str` (required)
   - **Routes to:** Resume Service (`POST /inspect`)

2. **`analyze_job`**
   - **Description:** Analyze job description text and extract title, required skills, and experience requirements.
   - **Arguments:** `job_description: str` (required)
   - **Routes to:** Job Service (`POST /analyze`)

3. **`compare_skills`**
   - **Description:** Compare candidate skills against job required skills and calculate match percentage.
   - **Arguments:** `candidate_skills: list[str]`, `required_skills: list[str]` (required)
   - **Routes to:** Matching Service (`POST /compare`)

---

## 14. Phase 3 — Composite MCP Capabilities

In real enterprise systems, an AI agent often needs high-level business answers rather than performing multiple micro-steps manually. **Composite MCP Capabilities** orchestrate multiple lower-level microservices inside the gateway and return a single, rich, unified result.

```text
             MCP CLIENT
                 |
                 v
          MCP GATEWAY :8000
                 |
      +----------+----------+
      |          |          |
      v          v          v
   Resume      Job       Matching
   :8001       :8002       :8003
```

### Atomic vs. Composite Capabilities

```text
[Atomic Capability]
inspect_resume ──────────> Resume Service (:8001)

[Composite Capability 1: generate_candidate_report]
generate_candidate_report ──┬──> Resume Service (:8001/inspect)
                            ├──> Job Service (:8002/analyze)
                            └──> Matching Service (:8003/compare)
                            ───> Combined Unified Assessment

[Composite Capability 2: create_candidate_shortlist]
create_candidate_shortlist ─┬──> Job Service (:8002/analyze)
                            ├──> Loop Resumes (Resume :8001/inspect)
                            ├──> Loop Matches (Matching :8003/compare)
                            └──> Deterministic Ranked Shortlist
```

### Critical Architecture Rule: Direct Internal Orchestration
The MCP Gateway **does NOT recursively call itself through MCP**. Calling tools through JSON-RPC loops over network ports creates latency and protocol overhead. Instead, composite tools orchestrate private async helper functions (`_call_resume_service`, `_call_job_service`, `_call_matching_service`) that talk directly to backend REST APIs.

### The Two Composite Tools

4. **`generate_candidate_report`**
   - **Description:** Generate a comprehensive candidate evaluation report by orchestrating resume inspection, job analysis, and skill comparison.
   - **Inputs:** `resume_text: str`, `job_description: str`
   - **Returns:**
     ```json
     {
       "candidate": {
         "name": "Alex Johnson",
         "skills": ["Python", "SQL", "FastAPI", "Docker"],
         "experience_years": 4,
         "education": "B.Tech"
       },
       "job": {
         "title": "Backend Software Engineer",
         "required_skills": ["Python", "SQL", "REST API"],
         "experience_required": 3
       },
       "skill_match": {
         "matched": ["Python", "SQL"],
         "missing": ["REST API"],
         "match_percentage": 66.67
       },
       "overall_assessment": "Good technical match with some skill gaps. Experience requirement met (4 years vs 3 required)."
     }
     ```

5. **`create_candidate_shortlist`**
   - **Description:** Evaluate multiple candidate resumes against a job description and generate a ranked candidate shortlist.
   - **Inputs:** `job_description: str`, `resumes: list[str]`
   - **Ranking Algorithm:**
     - **Primary:** `match_percentage` (descending)
     - **Secondary (Tie-breaker):** `experience_years` (descending)
     - Sequential ranks assigned starting at 1.
   - **Returns:**
     ```json
     {
       "job": {
         "title": "Backend Software Engineer",
         "required_skills": ["Python", "SQL", "REST API"],
         "experience_required": 3
       },
       "candidates": [
         {
           "rank": 1,
           "name": "Candidate Gamma",
           "match_percentage": 100.0,
           "matched_skills": ["Python", "SQL", "REST API"],
           "missing_skills": [],
           "experience_years": 6
         },
         {
           "rank": 2,
           "name": "Candidate Alpha",
           "match_percentage": 66.67,
           "matched_skills": ["Python", "SQL"],
           "missing_skills": ["REST API"],
           "experience_years": 5
         }
       ],
       "total_candidates": 2
     }
     ```

---

## 15. Single Correlation ID Tracing for Composite Workflows

When a composite capability is executed, the gateway generates **one correlation ID** representing the entire business transaction. Every backend call made across all microservices carries this exact same `X-Request-ID`:

```text
MCP Client (tools/call: generate_candidate_report)
    │
    ▼
MCP Gateway: generates [mcp-req-report-c66a69f3]
             logs: [mcp-req-report-c66a69f3] tool=generate_candidate_report started
    │
    ├── [mcp-req-report-c66a69f3] POST :8001/inspect ──> Resume Service logs: [mcp-req-report-c66a69f3] POST /inspect 200
    ├── [mcp-req-report-c66a69f3] POST :8002/analyze ──> Job Service logs   : [mcp-req-report-c66a69f3] POST /analyze 200
    └── [mcp-req-report-c66a69f3] POST :8003/compare ──> Matching Service logs: [mcp-req-report-c66a69f3] POST /compare 200
    │
    ▼
MCP Gateway: logs: [mcp-req-report-c66a69f3] tool=generate_candidate_report completed
    │
    ▼
MCP Client receives unified composite report
```

---

## 16. Comprehensive Verification Suite

Run the full end-to-end automated test suite:

```powershell
.\.venv\Scripts\python.exe test_mcp_gateway.py
```

This suite validates:
1. **Tool Discovery:** Exactly 5 tools exposed with valid JSON schemas.
2. **Atomic Tools:** `inspect_resume`, `analyze_job`, `compare_skills`.
3. **Composite Report:** Full orchestration across 3 services.
4. **Candidate Shortlist:** Multi-candidate evaluation with Candidate C ranked #1 (100% match, 6 yrs).
5. **Tie-Breaking:** Equal match percentage broken by higher experience years.
6. **Input Validation:** Clean `[INVALID_INPUT]` semantic errors without stack trace leakage.
7. **Correlation ID Consistency:** Verified via console logs.

> **MCP Inspector Note:** MCP Inspector was not executed via `npx` because Node.js/npx is not installed on this machine. MCP protocol compliance, tool discovery, and routing behavior are fully verified using the official Python MCP client.
