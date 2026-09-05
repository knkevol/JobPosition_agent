from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.services.fit_score_calculator import compute_skill_match_rate, calculate_fit_score
from app.services.user_service import get_or_create_default_user
from app.models.job_posting import JobPosting
from app.models.resume_profile import ResumeProfile
from app.models.portfolio_project import PortfolioProject
from app.models.fit_score import FitScore
from app.schemas.fit_score import FitScoreOut

router = APIRouter(prefix="/fit-scores", tags=["fit-scores"])

class FitScoreCalculateRequest(BaseModel):
    job_posting_id: int

# 분석된 이력서의 skills + self_reported_tech + 포트폴리오 tech_stack
def _collect_user_skills(db: Session, user_id: int) -> list[str]:
    resume = (
        db.query(ResumeProfile)
        .filter(ResumeProfile.user_id == user_id)
        .order_by(ResumeProfile.created_at.desc())
        .first()
    )
    if resume is None:
        raise HTTPException(status_code=422, detail="분석된 이력서가 없습니다. 이력서를 업로드 해주세요.")

    portfolios = db.query(PortfolioProject).filter(PortfolioProject.user_id == user_id).all()

    all_skills = list(resume.skills) + list(resume.self_reported_tech)
    for project in portfolios:
        all_skills.extend(project.tech_stack)

    # dict.fromkeys : 중복 제거 + 순서 유지
    return list(dict.fromkeys(all_skills))

@router.post("/calculate")
def calculate(payload: FitScoreCalculateRequest, db: Session = Depends(get_db)):
    user = get_or_create_default_user(db)

    job_posting = (
        db.query(JobPosting)
        .filter(JobPosting.id == payload.job_posting_id, JobPosting.user_id == user.id)
        .first()
    )
    if job_posting is None:
        raise HTTPException(status_code=404, detail="해당 채용공고 분석 결과가 없습니다.")

    user_skills = _collect_user_skills(db, user.id)

    base_score = compute_skill_match_rate(
        user_skills=user_skills,
        required_skills=job_posting.required_skills,
        preferred_skills=job_posting.preferred_skills,
    )
    result = calculate_fit_score(user_skills, job_posting, base_score)

    fit_score = (
        db.query(FitScore)
        .filter(FitScore.user_id == user.id, FitScore.job_id == job_posting.id)
        .first()
    )
    if fit_score is None:
        fit_score = FitScore(user_id=user.id, job_id=job_posting.id)
        db.add(fit_score)

    fit_score.score = result.score
    fit_score.matched_skills = result.matched_skills
    fit_score.missing_skills = result.missing_skills
    fit_score.reason = result.reason
    fit_score.grade = result.grade

    db.commit()
    db.refresh(fit_score)

    return{
        "fit_score_id": fit_score.id,
        "base_score": base_score,
        "result": result.model_dump(),
    }

@router.get("/{fit_score_id}", response_model=FitScoreOut)
def get_fit_score(fit_score_id: int, db: Session = Depends(get_db)):
    fit_score = db.get(FitScore, fit_score_id)
    if fit_score is None:
        raise HTTPException(status_code=404, detail="해당 적합도 평가 결과가 없습니다.")
    return fit_score