from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import func, and_
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.services.job_posting_fetcher import fetch_page_text
from app.services.job_posting_analyzer import analyze_job_posting_text
from app.services.user_service import get_or_create_default_user
from app.models.job_posting import JobPosting, ApplicationStatus
from app.models.fit_score import FitScore, FitGrade
from app.models.user_feedback import UserFeedback, FeedbackAction
from app.schemas.job_posting import JobPostingListItem, JobPostingDetailOut, ApplicationStatusUpdate
from app.schemas.fit_score import FitScoreOut
from app.schemas.feedback import FeedbackRequest, FeedbackOut

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

# 분석된 채용공고 목록을 적합도/회사/직무/부족기술 기준으로 정렬 및 필터링
@router.get("", response_model=list[JobPostingListItem])
def list_job_postings(
    sort_by: Literal["score", "company", "title", "missing_count", "created_at"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
    grade: Optional[FitGrade] = None,
    company: Optional[str] = None,
    min_score: Optional[int] = None,
    application_status: Optional[ApplicationStatus] = None,
    feedback: Optional[FeedbackAction] = None,
    missing_skill: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    user = get_or_create_default_user(db)

    # UserFeedback은 이력이 쌓이는 이벤트 로그 테이블이기때문에 가장 최근 행만 남기면 해당 공고에 대한 관심 상태를 알 수 있다.
    ranked_feedback = (
        db.query(
            UserFeedback.job_id,
            UserFeedback.action,
            func.row_number().over(
                partition_by=UserFeedback.job_id,
                order_by=UserFeedback.created_at.desc(),
            ).label("rn"),
        )
        .filter(UserFeedback.user_id == user.id)
        .subquery()
    )
    latest_feedback = (
        db.query(ranked_feedback.c.job_id, ranked_feedback.c.action).filter(ranked_feedback.c.rn == 1).subquery()
    )

    # 적합도 계산을 안한 공고도 목록에서 빠지지 않도록
    query = (
        db.query(JobPosting, FitScore, latest_feedback.c.action)
        .outerjoin(FitScore, and_(FitScore.job_id == JobPosting.id, FitScore.user_id == user.id))
        .outerjoin(latest_feedback, latest_feedback.c.job_id == JobPosting.id)
        .filter(JobPosting.user_id == user.id)
    )

    if grade is not None:
        query = query.filter(FitScore.grade == grade)
    if company:
        query = query.filter(JobPosting.company.ilike(f"%{company}%"))
    if min_score is not None:
        query = query.filter(FitScore.score >= min_score)
    if application_status is not None:
        query = query.filter(JobPosting.application_status == application_status)
    if feedback is not None:
        query = query.filter(latest_feedback.c.action == feedback)
    if missing_skill:
        query = query.filter(FitScore.missing_skills.any(missing_skill)) # ARRAY 컬럼.any(값) : "값 = ANY(배열)" — missing_skills 배열 안에 이 문자열이 있는 행만

    sort_columns = {
        "score": FitScore.score,
        "company": JobPosting.company,
        "title": JobPosting.title,
        # array_length(배열, 1) : 1차원 배열의 원소 개수 (부족 기술이 몇 개인지)
        "missing_count": func.array_length(FitScore.missing_skills, 1),
        "created_at": JobPosting.created_at,
    }

    order_col = sort_columns[sort_by]
    # 적합도 None 공고 항상 맨 뒤로
    query = query.order_by(order_col.desc().nullslast() if order == "desc" else order_col.asc().nullslast())
    rows = query.offset(offset).limit(limit).all()

    return [
        JobPostingListItem(
            id=job.id,
            company=job.company,
            title=job.title,
            application_status=job.application_status,
            created_at=job.created_at,
            fit_score=fit_score.score if fit_score else None,
            fit_grade=fit_score.grade if fit_score else None,
            missing_skills_count=len(fit_score.missing_skills) if fit_score else None,
            feedback=feedback_action,
        )
        for job, fit_score, feedback_action in rows
    ]

# 공고 상세정보 반환 : 일치/부족 역랑, 추천 이유, 관심/지원 상태 등
@router.get("/{job_posting_id}", response_model=JobPostingDetailOut)
def get_job_posting_detail(job_posting_id: int, db: Session = Depends(get_db)):
    user = get_or_create_default_user(db)
    job_posting = (db.query(JobPosting).filter(JobPosting.id == job_posting_id, JobPosting.user_id == user.id).first())

    if job_posting is None:
        raise HTTPException(status_code=404, detail="해당 채용공고 분석 결과가 없습니다.")

    fit_score = (db.query(FitScore).filter(FitScore.job_id == job_posting_id, FitScore.user_id == user.id).first())
    latest_feedback = (db.query(UserFeedback).filter(UserFeedback.job_id == job_posting_id, UserFeedback.user_id == user.id).order_by(UserFeedback.created_at.desc()).first())

    return JobPostingDetailOut(
        id=job_posting.id,
        company=job_posting.company,
        title=job_posting.title,
        url=job_posting.url,
        required_skills=job_posting.required_skills,
        preferred_skills=job_posting.preferred_skills,
        experience_level=job_posting.experience_level,
        source_site=job_posting.source_site,
        application_status=job_posting.application_status,
        created_at=job_posting.created_at,
        feedback=latest_feedback.action if latest_feedback else None,
        fit_score=FitScoreOut.model_validate(fit_score) if fit_score else None,
    )

# 관심/제외 표시. 이력 보존
@router.post("/{job_posting_id}/feedback", response_model=FeedbackOut)
def add_feedback(job_posting_id: int, payload: FeedbackRequest, db: Session = Depends(get_db)):
    user = get_or_create_default_user(db)
    job_posting = (db.query(JobPosting).filter(JobPosting.id == job_posting_id, JobPosting.user_id == user.id).first())

    if job_posting is None:
        raise HTTPException(status_code=404, detail="해당 채용공고 분석 결과가 없습니다.")

    feedback = UserFeedback(user_id=user.id, job_id=job_posting_id, action=payload.action)
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback

@router.patch("/{job_posting_id}/application-status")
def update_application_status(job_posting_id: int, payload: ApplicationStatusUpdate, db: Session = Depends(get_db)):
    user = get_or_create_default_user(db)
    job_posting = (db.query(JobPosting).filter(JobPosting.id == job_posting_id, JobPosting.user_id == user.id).first())

    if job_posting is None:
        raise HTTPException(status_code=404, detail="해당 채용공고 분석 결과가 없습니다.")

    job_posting.application_status = payload.application_status
    db.commit()
    db.refresh(job_posting)
    return {"job_posting_id": job_posting.id, "application_status": job_posting.application_status}