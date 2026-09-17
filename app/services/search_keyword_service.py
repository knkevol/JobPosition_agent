from collections import Counter

from sqlalchemy.orm import Session

from app.models.resume_profile import ResumeProfile
from app.models.portfolio_version import PortfolioVersion
from app.models.search_keyword_cache import SearchKeywordCache
from app.models.user_feedback import UserFeedback, FeedbackAction
from app.models.job_posting import JobPosting
from app.models.user import User
from app.services.search_keyword_generator import generate_search_keywords

# 관심(❤️) 표시한 공고들의 필수/우대 기술을 빈도순으로 정리해서, 키워드 생성 프롬프트에 넣을 문자열 생성
# 두번째 반환값(가장 최신 피드백 id)은 캐시 무효화 판단에 쓰인다.
def _build_liked_hint(db: Session, user_id: int) -> tuple[str, int | None]:
    rows = (
        db.query(UserFeedback.id, JobPosting.required_skills, JobPosting.preferred_skills)
        .join(JobPosting, JobPosting.id == UserFeedback.job_id)
        .filter(UserFeedback.user_id == user_id, UserFeedback.action == FeedbackAction.INTERESTED)
        .all()
    )
    if not rows:
        return "", None

    max_id = max(row.id for row in rows)
    skill_counter = Counter()
    for _id, required, preferred in rows:
        skill_counter.update(required)
        skill_counter.update(preferred)

    hint_lines = "\n".join(f"- {skill} ({count}회)" for skill, count in skill_counter.most_common())
    return hint_lines, max_id


# 활성화된 이력서/포트폴리오 버전이 마지막으로 키워드를 생성했을 때와 같고, 그 이후 새로 관심
# 표시한 공고도 없으면 캐시 재사용. 셋 중 하나라도 바뀌었으면 LLM으로 새로 생성.
def get_search_keywords(db: Session, user: User, skill_frequency: list[tuple[str, int]], experience_context: str) -> tuple[list[str], bool]:
    resume = (
        db.query(ResumeProfile)
        .filter(ResumeProfile.user_id == user.id, ResumeProfile.is_active.is_(True))
        .first()
    )
    active_version = (
        db.query(PortfolioVersion)
        .filter(PortfolioVersion.user_id == user.id, PortfolioVersion.is_active.is_(True))
        .first()
    )
    portfolio_version_id = active_version.id if active_version else None

    liked_hint, max_liked_id = _build_liked_hint(db, user.id)

    cache = db.query(SearchKeywordCache).filter(SearchKeywordCache.user_id == user.id).first()

    if (
        cache is not None
        and cache.resume_id == resume.id
        and cache.portfolio_version_id == portfolio_version_id
        and cache.last_liked_feedback_id == max_liked_id
    ):
        return cache.keywords, False

    keywords = generate_search_keywords(skill_frequency, experience_context, liked_hint)

    if cache is None:
        cache = SearchKeywordCache(user_id=user.id)
        db.add(cache)

    cache.resume_id = resume.id
    cache.portfolio_version_id = portfolio_version_id
    cache.last_liked_feedback_id = max_liked_id
    cache.keywords = keywords
    db.commit()

    return keywords, True