from sqlalchemy.orm import Session

from app.models.job_posting import JobPosting
from app.models.user import User
from app.services.job_posting_fetcher import fetch_page_text
from app.services.job_posting_analyzer import analyze_job_posting_text

class NotRelevantError(Exception):
    pass

class ExcludedByKeywordError(Exception):
    pass

def detect_source_site(url: str) -> str:
    if "saramin.co.kr" in url:
        return "saramin"
    if "jobkorea.co.kr" in url:
        return "jobkorea"
    return "unknown"

# 공고 본문과 보유한 기술 스택 비교
def _is_relevant(text: str, relevant_terms: list[str]) -> bool:
    lowered = text.lower()
    return any(term.strip().lower() in lowered for term in relevant_terms if term.strip())

def _matches_excluded(text: str, exclude_keywords: list[str]) -> str | None:
    lowered = text.lower()
    for keyword in exclude_keywords:
        if keyword.strip() and keyword.strip().lower() in lowered:
            return keyword
    return None

# URL을 받아 분석된적 있을 시 기존행, 없으면 새로 분석해서 만든 행 반환
def analyze_or_get_existing(db: Session, user: User, url: str, relevant_terms: list[str] | None = None, exclude_keywords: list[str] | None = None) -> tuple[JobPosting, bool]:
    existing = (
        db.query(JobPosting)
        .filter(JobPosting.user_id == user.id, JobPosting.url == url)
        .first()
    )
    if existing is not None:
        return existing, True
    
    text = fetch_page_text(url)

    if relevant_terms is not None and not _is_relevant(text, relevant_terms):
        raise NotRelevantError(f"보유 기술 스택과 무관: {url}")

    if exclude_keywords:
        matched = _matches_excluded(text, exclude_keywords)
        if matched:
            raise ExcludedByKeywordError(f"제외 키워드 '{matched}'와 일치: {url}")
        
    extracted = analyze_job_posting_text(text)

    posting = JobPosting(user_id=user.id, url=url)
    posting.company = extracted.company
    posting.title = extracted.title
    posting.required_skills = extracted.required_skills
    posting.preferred_skills = extracted.preferred_skills
    posting.experience_level = extracted.experience_level
    posting.source_site = detect_source_site(url)
    db.add(posting)

    db.commit()
    db.refresh(posting)

    return posting, False