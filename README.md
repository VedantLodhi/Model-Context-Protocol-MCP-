# Talent Intelligence MCP Gateway (Backend Services)

Welcome to the **Talent Intelligence MCP Gateway** learning project! This repository contains the backend microservice foundation designed to gain hands-on experience with the Model Context Protocol (MCP).

---

## 1. Project Overview

The Talent Intelligence project demonstrates how an intelligent agent or client (e.g., Claude Desktop, MCP Inspector, or any AI assistant) can interact with diverse backend HR and talent systems using a single unified protocol: the **Model Context Protocol (MCP)**.

In this initial phase, we establish the three core backend REST APIs that our future **MCP Gateway** will coordinate and call.

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

### Conceptual MCP Architecture (Future Phase)
```text
                  MCP Client / MCP Inspector
                              |
                              | MCP Protocol
                              v
                     +------------------+
                     |   MCP Gateway    |
                     |                  |
                     | Discovery        |
                     | Authentication   |
                     | Authorization    |
                     | Routing          |
                     | Logging          |
                     +--------+---------+
                              |
                 +------------+------------+
                 |            |            |
                 v            v            v
           Resume API     Job API     Matching API
             :8001          :8002         :8003
```

### Direct Gateway Routing Preview
```text
MCP Client
    |
    v
MCP Gateway
    |
    +----> Resume API   (:8001)
    |
    +----> Job API      (:8002)
    |
    +----> Matching API (:8003)
```

> **IMPORTANT:** These are standalone **BACKEND REST APIs**, NOT MCP tools yet. The MCP Gateway and its 5 MCP tools (`inspect_resume`, `analyze_job`, `compare_skills`, `generate_candidate_report`, `create_candidate_shortlist`) will be implemented in the next phase.

---

## 4. Installation Requirements

- **Operating System:** Windows 10/11, macOS, or Linux
- **Python:** Version 3.11 or newer (Python 3.12 recommended)
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

# Or on Command Prompt:
# .\.venv\Scripts\activate.bat
```

---

## 8. Dependency Installation

With the virtual environment activated, install the minimal required packages:

```powershell
pip install -r requirements.txt
```

Verify installed packages:
```powershell
pip list
```

Installed packages:
- `fastapi` — High-performance modern web framework
- `uvicorn` — Lightning-fast ASGI web server
- `pydantic` — Data validation and parsing
- `httpx` — Modern HTTP client for future service-to-service calls

---

## 9. How to Start Each Service

Open three separate terminals (or run as background processes), activate `.venv`, and start each service:

### Terminal 1: Resume Service (Port 8001)
```powershell
.\.venv\Scripts\python.exe -m uvicorn services.resume_service.main:app --port 8001 --reload
```

### Terminal 2: Job Service (Port 8002)
```powershell
.\.venv\Scripts\python.exe -m uvicorn services.job_service.main:app --port 8002 --reload
```

### Terminal 3: Matching Service (Port 8003)
```powershell
.\.venv\Scripts\python.exe -m uvicorn services.matching_service.main:app --port 8003 --reload
```

---

## 10. Port Mapping

| Service Name | Port | Base URL | Primary Endpoint |
|---|---|---|---|
| **Resume Service** | `8001` | `http://localhost:8001` | `POST /inspect` |
| **Job Service** | `8002` | `http://localhost:8002` | `POST /analyze` |
| **Matching Service** | `8003` | `http://localhost:8003` | `POST /compare` |

---

## 11. Health Endpoints

Each service exposes a simple health probe returning HTTP 200:

- `GET http://localhost:8001/health`
- `GET http://localhost:8002/health`
- `GET http://localhost:8003/health`

Sample response:
```json
{
  "status": "ok",
  "service": "resume-service"
}
```

---

## 12. Interactive API Documentation URLs

FastAPI automatically generates interactive OpenAPI / Swagger documentation:

- **Resume Service Docs:** [http://localhost:8001/docs](http://localhost:8001/docs)
- **Job Service Docs:** [http://localhost:8002/docs](http://localhost:8002/docs)
- **Matching Service Docs:** [http://localhost:8003/docs](http://localhost:8003/docs)

---

## 13. Example `curl` Requests

### Inspect Resume (`:8001`)
```bash
curl -X POST http://localhost:8001/inspect \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: req-inspect-001" \
  -d "{\"resume_text\": \"Alex Johnson is a backend developer with 4 years of experience. He has worked with Python, SQL, FastAPI and Docker. He completed B.Tech.\"}"
```

### Analyze Job (`:8002`)
```bash
curl -X POST http://localhost:8002/analyze \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: req-job-001" \
  -d "{\"job_description\": \"We are looking for a Backend Software Engineer with 3+ years of experience. Required skills: Python, SQL and REST API.\"}"
```

### Compare Skills (`:8003`)
```bash
curl -X POST http://localhost:8003/compare \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: req-match-001" \
  -d "{\"candidate_skills\": [\"Python\", \"SQL\"], \"required_skills\": [\"Python\", \"SQL\", \"REST API\"]}"
```

---

## 14. Example PowerShell `Invoke-RestMethod` Requests

### Inspect Resume
```powershell
$body = @{
    resume_text = "Alex Johnson is a backend developer with 4 years of experience. He has worked with Python, SQL, FastAPI and Docker. He completed B.Tech."
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8001/inspect" -Method Post -Body $body -ContentType "application/json" -Headers @{"X-Request-ID"="ps-resume-01"}
```

### Analyze Job
```powershell
$body = @{
    job_description = "We are looking for a Backend Software Engineer with 3+ years of experience. Required skills: Python, SQL and REST API."
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8002/analyze" -Method Post -Body $body -ContentType "application/json" -Headers @{"X-Request-ID"="ps-job-01"}
```

### Compare Skills
```powershell
$body = @{
    candidate_skills = @("Python", "SQL")
    required_skills  = @("Python", "SQL", "REST API")
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8003/compare" -Method Post -Body $body -ContentType "application/json" -Headers @{"X-Request-ID"="ps-match-01"}
```

---

## 15. Standardized Response Formats

Every API responds with a unified standard envelope:

### Success Envelope
```json
{
  "success": true,
  "data": {
    "candidate_name": "Alex Johnson",
    "skills": ["Python", "SQL", "FastAPI", "Docker"],
    "experience_years": 4,
    "education": "B.Tech"
  },
  "error": null
}
```

### Matching Calculation Result
```json
{
  "success": true,
  "data": {
    "matched": ["Python", "SQL"],
    "missing": ["REST API"],
    "match_percentage": 66.67
  },
  "error": null
}
```

### Error Envelope (e.g. Validation Failure / HTTP 422)
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "INVALID_INPUT",
    "message": "resume_text: Field required"
  }
}
```

---

## 16. How Request / Correlation IDs Work

Each service includes a lightweight `RequestIdMiddleware`:
1. When an incoming request contains the `X-Request-ID` header, that ID is captured and reused.
2. If no `X-Request-ID` header is present, the service automatically generates an 8-character identifier.
3. The ID is attached to the outgoing response in the `X-Request-ID` header.
4. Each service logs the start and finish of every request with the correlated ID:
   ```text
   [req-inspect-001] POST /inspect
   [req-inspect-001] completed 200
   ```
This provides request tracing across services without requiring complex distributed tracing agents.

---

## 17. How the Future MCP Gateway Will Sit in Front of These APIs

In Phase 2, we will create the **MCP Gateway**:
- The MCP Gateway will connect to these three REST APIs using the endpoints defined in `config.py`.
- Instead of exposing raw REST endpoints to the AI, the Gateway translates these microservice calls into 5 semantic MCP Tools:
  1. `inspect_resume`
  2. `analyze_job`
  3. `compare_skills`
  4. `generate_candidate_report`
  5. `create_candidate_shortlist`
- The Gateway handles discovery, authentication, authorization, routing, and error translation, allowing any MCP client to conduct talent intelligence tasks through a standard protocol.

---

## 18. Architectural Clarification

> **EXPLICIT BOUNDARY:** The services currently in this repository are **pure backend REST microservices**. They do NOT run the MCP protocol yet, do not use Docker, do not use external databases, and do not make LLM calls. They provide the reliable, deterministic foundation upon which the MCP Gateway will operate.
