
"""Job API Service running on Port 8002."""

import re
from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from services.common import StandardResponse, setup_common_handlers


app = FastAPI(
    title="Job API",
    description="Backend service for real job description analysis and requirement extraction.",
    version="1.1.0",
)

setup_common_handlers(app)


KNOWN_TITLES = [
    "Backend Software Engineer",
    "Frontend Engineer",
    "Full Stack Developer",
    "Data Engineer",
    "DevOps Engineer",
    "Software Engineer",
    "Software Developer",
    "Backend Developer",
    "Frontend Developer",
    "Full Stack Engineer",
    "Data Scientist",
    "Machine Learning Engineer",
    "Python Developer",
    "Java Developer",
    "React Developer",
    "Cloud Engineer",
]


KNOWN_SKILLS = [
    "Python",
    "SQL",
    "REST API",
    "FastAPI",
    "Docker",
    "AWS",
    "React",
    "Java",
    "JavaScript",
    "TypeScript",
    "C++",
    "C#",
    "Node.js",
    "PostgreSQL",
    "MySQL",
    "MongoDB",
    "Git",
    "Kubernetes",
    "Azure",
    "GCP",
    "Spring Boot",
    "Django",
    "Flask",
    "Angular",
    "Vue.js",
    "Redis",
    "Kafka",
    "Terraform",
    "Linux",
]


class AnalyzeJobRequest(BaseModel):
    job_description: str = Field(
        ...,
        min_length=1,
        description="Raw text of the job description",
    )


class JobData(BaseModel):
    title: Optional[str] = None
    required_skills: List[str] = []
    experience_required: Optional[int] = None
    description_length: int


class JobResponse(StandardResponse[JobData]):
    pass


class HealthResponse(BaseModel):
    status: str
    service: str


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "job-service"}


def extract_title(text: str) -> Optional[str]:
    """
    Extract a job title from an explicitly labelled title first,
    then fall back to known title phrases.
    """

    # Explicit forms:
    # Job Title: Python Backend Developer
    # Position: Python Backend Developer
    # Role: Python Backend Developer

    labeled_match = re.search(
        r"(?im)^\s*(?:job\s+title|position|role)\s*[:\-]\s*(.+?)\s*$",
        text,
    )

    if labeled_match:
        title = labeled_match.group(1).strip()

        if title:
            return title

    # Fall back only when no explicit title is present.
    text_lower = text.lower()

    for known_title in KNOWN_TITLES:
        if re.search(
            r"(?<!\w)" + re.escape(known_title.lower()) + r"(?!\w)",
            text_lower,
        ):
            return known_title

    return None


def extract_skills(text: str) -> List[str]:
    """
    Extract skills actually present in the job description.
    """

    text_lower = text.lower()
    found_skills = []

    for skill in KNOWN_SKILLS:
        pattern = r"(?<!\w)" + re.escape(skill.lower()) + r"(?!\w)"

        if re.search(pattern, text_lower):
            found_skills.append(skill)

    return found_skills


def extract_experience_required(text: str) -> Optional[int]:
    """
    Extract the minimum experience requirement.

    Examples recognized:
        3 years experience
        3+ years of experience
        5 yrs experience
        minimum 4 years
        2 years of professional experience
    """

    patterns = [
        r"(?:minimum|min\.?|at\s+least)\s+(\d+)\+?\s*(?:years?|yrs?)",
        r"(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:professional\s+)?experience",
        r"experience\s*(?:of|:)?\s*(\d+)\+?\s*(?:years?|yrs?)",
    ]

    matches = []

    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            matches.append(int(match.group(1)))

    if not matches:
        return None

    # If several requirements are present, use the largest stated
    # minimum requirement as the conservative requirement.
    return max(matches)


def analyze_job_text(text: str) -> JobData:
    """Analyze the actual job description text."""

    cleaned_text = text.strip()

    return JobData(
        title=extract_title(cleaned_text),
        required_skills=extract_skills(cleaned_text),
        experience_required=extract_experience_required(cleaned_text),
        description_length=len(cleaned_text),
    )


@app.post("/analyze", response_model=JobResponse)
def analyze_job(request: AnalyzeJobRequest):
    """Analyze an actual job description."""

    data = analyze_job_text(request.job_description)

    return JobResponse(
        success=True,
        data=data,
        error=None,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "services.job_service.main:app",
        host="0.0.0.0",
        port=8002,
        reload=False,
    )

