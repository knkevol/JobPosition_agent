from sqlalchemy.orm import Session

from collections import Counter

from app.models.resume_profile import ResumeProfile
from app.models.portfolio_version import PortfolioVersion
from app.models.job_posting import JobPosting
from app.models.fit_score import FitScore
from app.models.user import User
from app.services.fit_score_calculator import compute_skill_match_rate, calculate_fit_score

# 활성화된 이력서가 없을 때 전용 예외. HTTP와 무관한 스크립트에서도 호출되기 때문에 HTTPException사용 안함
class NoActiveResumeError(Exception):
    pass

# 이력서 skills + self_reported_tech + 포트폴리오 tech_stack
def collect_user_skills(db: Session, user_id: int) -> tuple[list[str], list[str], str, list[tuple[str, int]]]:
    resume = (
        db.query(ResumeProfile)
        .filter(ResumeProfile.user_id == user_id, ResumeProfile.is_active.is_(True))
        .first()
    )

    if resume is None:
        raise NoActiveResumeError("적합도 계산에 사용할 활성화된 이력서가 없습니다. 이력서를 저장하고 활성으로 지정해주세요.")

    active_version = (
        db.query(PortfolioVersion)
        .filter(PortfolioVersion.user_id == user_id, PortfolioVersion.is_active.is_(True))
        .first()
    )
    portfolios = active_version.projects if active_version else []

    self_reported_skills = list(resume.skills) + list(resume.self_reported_tech)
    for project in portfolios:
        self_reported_skills.extend(project.tech_stack)

    verified_skills = []
    for project in portfolios:
        if project.github_analysis is not None:
            verified_skills.extend(project.github_analysis.verified_tech)

    experience_lines = []
    for item in resume.experience:
        description = item.get("description")
        if description:
            experience_lines.append(f"- {item.get('company', '?')} ({item.get('period', '?')}) - {item.get('role', '?')}: {description}")
    experience_context = "\n".join(experience_lines)

    skill_frequency = Counter(self_reported_skills).most_common()

    return (
        list(dict.fromkeys(self_reported_skills)),
        list(dict.fromkeys(verified_skills)),
        experience_context,
        skill_frequency,
    )

# job_posting 하나에 대한 적합도를 계산해서 FitScore 행에 upsert(있으면 갱신, 없으면 생성)하고 (FitScore, base_score) 반환
def calculate_and_save_fitscore(db: Session, user: User, job_posting: JobPosting) -> tuple[FitScore, float]:
    self_reported_skills, verified_skills, experience_context, _skill_frequency = collect_user_skills(db, user.id)

    base_score = compute_skill_match_rate(
        verified_skills=verified_skills,
        self_reported_skills=self_reported_skills,
        required_skills=job_posting.required_skills,
        preferred_skills=job_posting.preferred_skills,
    )
    result = calculate_fit_score(verified_skills, self_reported_skills, job_posting, base_score, experience_context)

    fit_score = (db.query(FitScore).filter(FitScore.user_id == user.id, FitScore.job_id == job_posting.id).first())
    if fit_score is None:
        fit_score = FitScore(user_id=user.id, job_id=job_posting.id)
        db.add(fit_score)

    fit_score.score = result.score
    fit_score.matched_skills = result.matched_skills
    fit_score.verified_matched_skills = result.verified_matched_skills
    fit_score.unverified_matched_skills = result.unverified_matched_skills
    fit_score.missing_skills = result.missing_skills
    fit_score.reason = result.reason
    fit_score.grade = result.grade

    db.commit()
    db.refresh(fit_score)

    return fit_score, base_score