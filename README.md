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
                     | Exposed Semantic Tools:          |
                     |   - inspect_resume               |
                     |   - analyze_job                  |
                     |   - compare_skills               |
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

## 13. Phase 2 — MCP Gateway

### What MCP Does Here
The **Model Context Protocol (MCP)** provides an open, standardized bridge between AI clients (LLMs, agents, developer tools) and data sources/tools. Instead of building custom REST integrations for every tool or forcing an LLM to manage multiple HTTP URLs and authentication handshakes, the AI interacts with a single MCP server.

### Difference Between REST API and MCP Tool

| Aspect | Backend REST Endpoint (e.g., `POST /inspect`) | MCP Tool (e.g., `inspect_resume`) |
|---|---|---|
| **Target Consumer** | Software applications / microservices | AI models, LLM agents, MCP Clients |
| **Protocol** | HTTP / REST / JSON | JSON-RPC 2.0 over Streamable HTTP or Stdio |
| **Schema Discovery** | OpenAPI (`/docs`, `/openapi.json`) | MCP Protocol `tools/list` handshake |
| **Payload Envelope** | Transport envelope (`success`, `data`, `error`) | Direct semantic data (`candidate_name`, `skills`) |
| **Error Handling** | HTTP status codes (400, 422, 500) | MCP Protocol error objects (`is_error=True`) |

### How the MCP Gateway Routes Calls
1. The MCP client sends a `tools/call` JSON-RPC message targeting `inspect_resume`.
2. The MCP Gateway validates the input arguments according to the schema.
3. The Gateway generates an application-level correlation ID (e.g., `mcp-req-f6ee04ef`).
4. The Gateway invokes `call_backend()` via `httpx.AsyncClient` targeting `http://localhost:8001/inspect`, passing `X-Request-ID: mcp-req-f6ee04ef`.
5. The Resume Service processes the text deterministically and responds with `{ "success": true, "data": {...} }`.
6. The Gateway unwraps the `data` payload and delivers it directly to the MCP client as the tool execution result.

### Currently Exposed MCP Tools

1. **`inspect_resume`**
   - **Description:** Inspect and parse raw candidate resume text into structured candidate profile data.
   - **Arguments:** `resume_text: str` (required)
   - **Returns:** `{ "candidate_name": str, "skills": list[str], "experience_years": int, "education": str }`

2. **`analyze_job`**
   - **Description:** Analyze job description text and extract title, required skills, and experience requirements.
   - **Arguments:** `job_description: str` (required)
   - **Returns:** `{ "title": str, "required_skills": list[str], "experience_required": int }`

3. **`compare_skills`**
   - **Description:** Compare candidate skills against job required skills and calculate match percentage.
   - **Arguments:** `candidate_skills: list[str]`, `required_skills: list[str]` (required)
   - **Returns:** `{ "matched": list[str], "missing": list[str], "match_percentage": float }`

---

## 14. Testing the MCP Gateway

An automated verification script is provided using the official MCP Python Client:

```powershell
.\.venv\Scripts\python.exe test_mcp_gateway.py
```

This test script validates:
1. Connection to the Streamable HTTP transport at `http://127.0.0.1:8000/mcp`.
2. Protocol handshake and `tools/list` discovery for all 3 tools.
3. Automatic schema derivation from function type annotations.
4. Live tool execution (`tools/call`) across all 3 tools.
5. Verification of unwrapped semantic results.
6. Error translation on invalid input (clean error message without stack trace leakage).

> **MCP Inspector Note:** MCP Inspector was not executed via `npx` because Node.js/npx is not installed on this machine. MCP protocol compliance, tool discovery, and routing behavior are fully verified using the official Python MCP client.

---

## 15. How Request IDs & Tracing Work

The gateway separates:
- **MCP Protocol Identity:** Internal JSON-RPC request IDs handled by the MCP SDK.
- **Application Correlation ID:** Application-level tracing IDs formatted as `mcp-req-<uuid>`.

Tracing flow:
```text
MCP Client (tools/call: inspect_resume)
    |
    v
MCP Gateway: generates [mcp-req-f6ee04ef]
             logs: [mcp-req-f6ee04ef] tool=inspect_resume started
             logs: [mcp-req-f6ee04ef] calling resume-service
    |
    | HTTP POST /inspect
    | Header: X-Request-ID: mcp-req-f6ee04ef
    v
Resume Service :8001
             logs: [mcp-req-f6ee04ef] POST /inspect
             logs: [mcp-req-f6ee04ef] completed 200
    |
    v
MCP Gateway: logs: [mcp-req-f6ee04ef] tool=inspect_resume completed
    |
    v
MCP Client: receives structured candidate data
```
