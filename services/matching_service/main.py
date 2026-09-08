"""Matching API Service running on Port 8003."""

from typing import List
from fastapi import FastAPI
from pydantic import BaseModel, Field
from services.common import StandardResponse, setup_common_handlers

app = FastAPI(
    title="Matching API",
    description="Backend service for comparing candidate skills against job requirements.",
    version="1.0.0"
)

setup_common_handlers(app)


class CompareSkillsRequest(BaseModel):
    candidate_skills: List[str] = Field(..., description="List of candidate skills")
    required_skills: List[str] = Field(..., description="List of required skills")


class MatchingData(BaseModel):
    matched: List[str]
    missing: List[str]
    match_percentage: float


class MatchingResponse(StandardResponse[MatchingData]):
    pass


class HealthResponse(BaseModel):
    status: str
    service: str


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "matching-service"}


@app.post("/compare", response_model=MatchingResponse)
def compare_skills(request: CompareSkillsRequest):
    """Compare candidate skills against required skills using case-insensitive set matching."""
    cand_lower = {s.strip().lower() for s in request.candidate_skills if s.strip()}

    matched: List[str] = []
    missing: List[str] = []

    # Preserve required skill casing and formatting
    for req in request.required_skills:
        req_clean = req.strip()
        if not req_clean:
            continue
        if req_clean.lower() in cand_lower:
            if req_clean not in matched:
                matched.append(req_clean)
        else:
            if req_clean not in missing:
                missing.append(req_clean)

    total_required = len(matched) + len(missing)
    if total_required == 0:
        match_percentage = 100.0 if not request.required_skills else 0.0
    else:
        match_percentage = round((len(matched) / total_required) * 100, 2)

    data = MatchingData(
        matched=matched,
        missing=missing,
        match_percentage=match_percentage
    )

    return MatchingResponse(
        success=True,
        data=data,
        error=None
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.matching_service.main:app", host="0.0.0.0", port=8003, reload=False)
