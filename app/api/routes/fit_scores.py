from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.services.fit_score_service import calculate_and_save_fitscore, NoActiveResumeError
from app.services.user_service import get_or_create_default_user
from app.models.job_posting import JobPosting
from app.models.fit_score import FitScore
from app.schemas.fit_score import FitScoreOut

router = APIRouter(prefix="/fit-scores", tags=["fit-scores"])

class FitScoreCalculateRequest(BaseModel):
    job_posting_id: int

# 분석된 이력서의 skills + self_reported_tech + 포트폴리오 tech_stack
@router.post("/calculate")
def calculate(payload: FitScoreCalculateRequest, db: Session = Depends(get_db)):
    user = get_or_create_default_user(db)

    job_posting = (db.query(JobPosting).filter(JobPosting.id == payload.job_posting_id, JobPosting.user_id == user.id).first())
    if job_posting is None:
        raise HTTPException(status_code=404, detail="해당 채용공고 분석 결과가 없습니다.")

    try:
        fit_score, base_score = calculate_and_save_fitscore(db, user, job_posting)
    except NoActiveResumeError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return{
        "fit_score_id": fit_score.id,
        "base_score": base_score,
        "result": {
            "score": fit_score.score,
            "matched_skills": fit_score.matched_skills,
            "verified_matched_skills": fit_score.verified_matched_skills,
            "unverified_matched_skills": fit_score.unverified_matched_skills,
            "missing_skills": fit_score.missing_skills,
            "reason": fit_score.reason,
            "grade": fit_score.grade,
        },
    }

@router.get("/{fit_score_id}", response_model=FitScoreOut)
def get_fit_score(fit_score_id: int, db: Session = Depends(get_db)):
    fit_score = db.get(FitScore, fit_score_id)
    if fit_score is None:
        raise HTTPException(status_code=404, detail="해당 적합도 평가 결과가 없습니다.")
    return fit_score