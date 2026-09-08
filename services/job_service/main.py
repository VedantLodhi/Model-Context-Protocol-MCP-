"""Job API Service running on Port 8002."""

import re
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel, Field
from services.common import StandardResponse, setup_common_handlers

app = FastAPI(
    title="Job API",
    description="Backend service for job description analysis and skill requirement extraction.",
    version="1.0.0"
)

setup_common_handlers(app)

KNOWN_TITLES = [
    "Backend Software Engineer",
    "Frontend Engineer",
    "Full Stack Developer",
    "Data Engineer",
    "DevOps Engineer",
    "Software Engineer"
]

KNOWN_SKILLS = [
    "Python",
    "SQL",
    "REST API",
    "FastAPI",
    "Docker",
    "AWS",
    "React",
    "Java"
]


class AnalyzeJobRequest(BaseModel):
    job_description: str = Field(..., min_length=1, description="Raw text of the job description")


class JobData(BaseModel):
    title: str
    required_skills: List[str]
    experience_required: int


class JobResponse(StandardResponse[JobData]):
    pass


class HealthResponse(BaseModel):
    status: str
    service: str


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "job-service"}


@app.post("/analyze", response_model=JobResponse)
def analyze_job(request: AnalyzeJobRequest):
    """Analyze job description and extract title, required skills, and experience requirement."""
    text = request.job_description
    text_lower = text.lower()

    # Extract title
    title = "Backend Software Engineer"
    for known_title in KNOWN_TITLES:
        if re.search(r"\b" + re.escape(known_title.lower()) + r"\b", text_lower):
            title = known_title
            break

    # Extract skills
    found_skills = []
    for skill in KNOWN_SKILLS:
        if re.search(r"\b" + re.escape(skill.lower()) + r"\b", text_lower):
            found_skills.append(skill)

    if not found_skills:
        found_skills = ["Python", "SQL", "REST API"]

    # Extract experience required
    exp_match = re.search(r"(\d+)\+?\s*(?:years?|yrs?)", text, re.IGNORECASE)
    experience_required = int(exp_match.group(1)) if exp_match else 3

    data = JobData(
        title=title,
        required_skills=found_skills,
        experience_required=experience_required
    )

    return JobResponse(
        success=True,
        data=data,
        error=None
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.job_service.main:app", host="0.0.0.0", port=8002, reload=False)
