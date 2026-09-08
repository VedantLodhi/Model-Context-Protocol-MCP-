"""Resume API Service running on Port 8001."""

import re
from typing import List, Optional
from fastapi import FastAPI
from pydantic import BaseModel, Field
from services.common import StandardResponse, setup_common_handlers

app = FastAPI(
    title="Resume API",
    description="Backend service for candidate resume inspection and deterministic parsing.",
    version="1.0.0"
)

setup_common_handlers(app)

KNOWN_SKILLS = [
    "Python",
    "SQL",
    "FastAPI",
    "Docker",
    "AWS",
    "React",
    "Java",
    "REST API"
]

KNOWN_EDUCATION = [
    "B.Tech",
    "M.Tech",
    "B.S.",
    "M.S.",
    "Bachelor",
    "Master",
    "Ph.D."
]


class InspectResumeRequest(BaseModel):
    resume_text: str = Field(..., min_length=1, description="Raw text of candidate resume")


class ResumeData(BaseModel):
    candidate_name: str
    skills: List[str]
    experience_years: int
    education: str


class ResumeResponse(StandardResponse[ResumeData]):
    pass


class HealthResponse(BaseModel):
    status: str
    service: str


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "resume-service"}


@app.post("/inspect", response_model=ResumeResponse)
def inspect_resume(request: InspectResumeRequest):
    """Inspect and extract structured information from resume text using deterministic mock logic."""
    text = request.resume_text

    # Extract name (check for common candidate names or pattern "First Last")
    name_match = re.search(r"\b([A-Z][a-z]+ [A-Z][a-z]+)\b", text)
    candidate_name = name_match.group(1) if name_match else "Alex Johnson"

    # Extract skills
    found_skills = []
    text_lower = text.lower()
    for skill in KNOWN_SKILLS:
        if re.search(r"\b" + re.escape(skill.lower()) + r"\b", text_lower):
            found_skills.append(skill)

    if not found_skills:
        found_skills = ["Python", "SQL"]

    # Extract experience years
    exp_match = re.search(r"(\d+)\+?\s*(?:years?|yrs?)", text, re.IGNORECASE)
    experience_years = int(exp_match.group(1)) if exp_match else 4

    # Extract education
    education = "B.Tech"
    for edu in KNOWN_EDUCATION:
        if re.search(r"\b" + re.escape(edu.lower()) + r"\b", text_lower):
            education = edu
            break

    data = ResumeData(
        candidate_name=candidate_name,
        skills=found_skills,
        experience_years=experience_years,
        education=education
    )

    return ResumeResponse(
        success=True,
        data=data,
        error=None
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.resume_service.main:app", host="0.0.0.0", port=8001, reload=False)
