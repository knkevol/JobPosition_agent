from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.services.job_posting_fetcher import fetch_page_text
from app.services.job_posting_analyzer import analyze_job_posting_text
from app.services.user_service import get_or_create_default_user
from app.models.job_posting import JobPosting

router = APIRouter(prefix="/job-postings", tags=["job-postings"])

class JobPostingAnalyzeRequest(BaseModel):
    url: str

def detect_source_site(url: str) -> str:
    if "saramin.co.kr" in url:
        return "saramin"
    if "jobkorea.co.kr" in url:
        return "jobkorea"
    if "wanted.co.kr" in url:
        return "wanted"
    return "unknown"

@router.post("/analyze")
def analyze_job_posting(payload: JobPostingAnalyzeRequest, db: Session = Depends(get_db)):
    try:
        text = fetch_page_text(payload.url)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    extracted = analyze_job_posting_text(text)
    user = get_or_create_default_user(db)

    # 분석된 적 있는 URL인지 확인
    posting = (
        db.query(JobPosting)
        .filter(JobPosting.user_id == user.id, JobPosting.url == payload.url)
        .first()
    )
    if posting is None:
        posting = JobPosting(user_id=user.id, url=payload.url)
        db.add(posting)

    posting.company = extracted.company
    posting.title = extracted.title
    posting.required_skills = extracted.required_skills
    posting.preferred_skills = extracted.preferred_skills
    posting.experience_level = extracted.experience_level
    posting.source_site = detect_source_site(payload.url)

    db.commit()
    db.refresh(posting)

    return {"job_posting_id": posting.id, "extracted": extracted.model_dump()}