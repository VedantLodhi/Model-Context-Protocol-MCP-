"""Verification test script for Talent Intelligence backend microservices."""

import json
import httpx

client = httpx.Client(timeout=10.0)

print("=== 1. HEALTH CHECKS ===")
for port, name in [(8001, "resume"), (8002, "job"), (8003, "matching")]:
    res = client.get(f"http://localhost:{port}/health")
    print(f"{name.upper()} ({port}): status={res.status_code}, body={res.json()}, x-req-id={res.headers.get('x-request-id')}")

print("\n=== 2. DOCS CHECKS ===")
for port, name in [(8001, "resume"), (8002, "job"), (8003, "matching")]:
    res = client.get(f"http://localhost:{port}/docs")
    print(f"{name.upper()} docs ({port}): status={res.status_code}")

print("\n=== 3. POST ENDPOINTS WITH SAMPLE DATA ===")

# 1. Resume
resume_payload = {
    "resume_text": "Alex Johnson is a backend developer with 4 years of experience. He has worked with Python, SQL, FastAPI and Docker. He completed B.Tech."
}
res_resume = client.post(
    "http://localhost:8001/inspect",
    json=resume_payload,
    headers={"X-Request-ID": "test-trace-resume-01"}
)
print(f"RESUME /inspect: status={res_resume.status_code}, header-req-id={res_resume.headers.get('x-request-id')}")
print(json.dumps(res_resume.json(), indent=2))

# 2. Job
job_payload = {
    "job_description": "We are looking for a Backend Software Engineer with 3+ years of experience. Required skills: Python, SQL and REST API."
}
res_job = client.post(
    "http://localhost:8002/analyze",
    json=job_payload,
    headers={"X-Request-ID": "test-trace-job-01"}
)
print(f"\nJOB /analyze: status={res_job.status_code}, header-req-id={res_job.headers.get('x-request-id')}")
print(json.dumps(res_job.json(), indent=2))

# 3. Matching
matching_payload = {
    "candidate_skills": ["Python", "SQL"],
    "required_skills": ["Python", "SQL", "REST API"]
}
res_match = client.post(
    "http://localhost:8003/compare",
    json=matching_payload,
    headers={"X-Request-ID": "test-trace-match-01"}
)
print(f"\nMATCHING /compare: status={res_match.status_code}, header-req-id={res_match.headers.get('x-request-id')}")
print(json.dumps(res_match.json(), indent=2))

print("\n=== 4. VALIDATION / ERROR ENVELOPE CHECKS ===")
# Invalid payload to resume (empty resume_text)
res_err = client.post("http://localhost:8001/inspect", json={"resume_text": ""})
print(f"RESUME invalid input: status={res_err.status_code}")
print(json.dumps(res_err.json(), indent=2))

# Missing field in matching
res_err2 = client.post("http://localhost:8003/compare", json={"candidate_skills": ["Python"]})
print(f"\nMATCHING missing field: status={res_err2.status_code}")
print(json.dumps(res_err2.json(), indent=2))
