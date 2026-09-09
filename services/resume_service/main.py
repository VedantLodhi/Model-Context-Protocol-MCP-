"""Resume API Service running on Port 8001."""

import re
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel, Field

from services.common import StandardResponse, setup_common_handlers


app = FastAPI(
    title="Resume API",
    description="Backend service for real resume text extraction and structured analysis.",
    version="1.1.0",
)

setup_common_handlers(app)


# Keep this vocabulary configurable and easy to extend.
KNOWN_SKILLS = [
    "Python",
    "SQL",
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
    "REST API",
    "Kubernetes",
    "Azure",
    "GCP",
]

KNOWN_EDUCATION = [
    "B.Tech",
    "M.Tech",
    "B.E.",
    "M.E.",
    "B.S.",
    "M.S.",
    "Bachelor",
    "Master",
    "Ph.D.",
    "MBA",
    "BCA",
    "MCA",
]


SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx"}


class InspectResumeRequest(BaseModel):
    resume_text: str = Field(
        ...,
        min_length=1,
        description="Raw text of candidate resume",
    )


class ResumeData(BaseModel):
    candidate_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = []
    experience_years: Optional[int] = None
    education: List[str] = []
    raw_text_length: int


class ResumeResponse(StandardResponse[ResumeData]):
    pass


class HealthResponse(BaseModel):
    status: str
    service: str


@app.get("/health", response_model=HealthResponse)
def health_check():
    return {"status": "ok", "service": "resume-service"}


def extract_email(text: str) -> Optional[str]:
    match = re.search(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        text,
    )
    return match.group(0) if match else None


def extract_phone(text: str) -> Optional[str]:
    match = re.search(
        r"(?<!\d)(?:\+?\d[\d\s().-]{8,}\d)(?!\d)",
        text,
    )
    return match.group(0).strip() if match else None


def extract_name(text: str) -> Optional[str]:
    """
    Deterministic candidate-name extraction.

    Priority:
    1. Explicit labels such as:
       Candidate Name: Vedant Lodhi
       Full Name: Vedant Lodhi
       Name: Vedant Lodhi

    2. Otherwise inspect the first few non-empty lines
       for a likely two-to-four-word person name.

    The labeled value is restricted to a single line so that
    the next resume field cannot accidentally become part of
    the candidate name.
    """

    labeled = re.search(
        r"(?im)^[ \t]*(?:candidate\s+name|full\s+name|name)"
        r"[ \t]*[:\-][ \t]*"
        r"([A-Za-z][A-Za-z.'-]*(?:[ \t]+[A-Za-z][A-Za-z.'-]*){0,3})"
        r"[ \t]*$",
        text,
    )

    if labeled:
        return labeled.group(1).strip()

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    for line in lines[:8]:

        if len(line) > 60:
            continue

        if any(char.isdigit() for char in line):
            continue

        words = line.split()

        if 2 <= len(words) <= 4 and all(
            re.match(
                r"^[A-Z][A-Za-z.'-]*$",
                word,
            )
            for word in words
        ):
            return line

    return None


def extract_skills(text: str) -> List[str]:
    text_lower = text.lower()
    found = []

    for skill in KNOWN_SKILLS:
        pattern = r"(?<!\w)" + re.escape(skill.lower()) + r"(?!\w)"

        if re.search(pattern, text_lower):
            found.append(skill)

    return found


def extract_experience_years(text: str) -> Optional[int]:
    matches = re.findall(
        r"(\d+)\+?\s*(?:years?|yrs?)",
        text,
        re.IGNORECASE,
    )

    if not matches:
        return None

    return max(int(value) for value in matches)


def extract_education(text: str) -> List[str]:
    text_lower = text.lower()
    found = []

    for education in KNOWN_EDUCATION:
        if re.search(
            r"(?<!\w)" + re.escape(education.lower()) + r"(?!\w)",
            text_lower,
        ):
            found.append(education)

    return found


def parse_resume_text(text: str) -> ResumeData:
    """Extract structured information from actual resume text."""

    cleaned_text = text.strip()

    return ResumeData(
        candidate_name=extract_name(cleaned_text),
        email=extract_email(cleaned_text),
        phone=extract_phone(cleaned_text),
        skills=extract_skills(cleaned_text),
        experience_years=extract_experience_years(cleaned_text),
        education=extract_education(cleaned_text),
        raw_text_length=len(cleaned_text),
    )


@app.post("/inspect", response_model=ResumeResponse)
def inspect_resume(request: InspectResumeRequest):
    """Analyze resume text supplied directly as JSON."""

    data = parse_resume_text(request.resume_text)

    return ResumeResponse(
        success=True,
        data=data,
        error=None,
    )


def extract_pdf_text(file_path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(file_path))

    pages = []

    for page in reader.pages:
        page_text = page.extract_text() or ""
        pages.append(page_text)

    return "\n".join(pages).strip()


def extract_docx_text(file_path: Path) -> str:
    from docx import Document

    document = Document(str(file_path))

    paragraphs = [paragraph.text for paragraph in document.paragraphs]

    return "\n".join(paragraphs).strip()


def extract_file_text(file_path: Path) -> str:
    extension = file_path.suffix.lower()

    if extension == ".txt":
        return file_path.read_text(encoding="utf-8", errors="ignore").strip()

    if extension == ".pdf":
        return extract_pdf_text(file_path)

    if extension == ".docx":
        return extract_docx_text(file_path)

    raise ValueError(f"Unsupported file type: {extension}")


@app.post("/inspect-file", response_model=ResumeResponse)
async def inspect_resume_file(file: UploadFile = File(...)):
    """
    Analyze an uploaded TXT, PDF, or DOCX resume.
    """

    if not file.filename:
        return ResumeResponse(
            success=False,
            data=None,
            error={
                "code": "INVALID_INPUT",
                "message": "A filename is required.",
            },
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        return ResumeResponse(
            success=False,
            data=None,
            error={
                "code": "DOCUMENT_UNSUPPORTED",
                "message": (
                    f"Unsupported file type '{extension}'. "
                    f"Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
                ),
            },
        )

    file_bytes = await file.read()

    if not file_bytes:
        return ResumeResponse(
            success=False,
            data=None,
            error={
                "code": "INVALID_INPUT",
                "message": "The uploaded file is empty.",
            },
        )

    # Use a temporary local file only for document parsing.
    import tempfile

    with tempfile.NamedTemporaryFile(
        suffix=extension,
        delete=False,
    ) as temp_file:
        temp_file.write(file_bytes)
        temp_path = Path(temp_file.name)

    try:
        text = extract_file_text(temp_path)

        if not text.strip():
            return ResumeResponse(
                success=False,
                data=None,
                error={
                    "code": "DOCUMENT_UNSUPPORTED",
                    "message": "No extractable text was found in the document.",
                },
            )

        data = parse_resume_text(text)

        return ResumeResponse(
            success=True,
            data=data,
            error=None,
        )

    except Exception as exc:
        # Return a controlled error without exposing stack traces.
        return ResumeResponse(
            success=False,
            data=None,
            error={
                "code": "DOCUMENT_PROCESSING_FAILED",
                "message": f"Unable to process the uploaded document: {type(exc).__name__}",
            },
        )

    finally:
        temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "services.resume_service.main:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
    )