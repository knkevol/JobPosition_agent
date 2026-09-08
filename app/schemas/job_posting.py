from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.job_posting import ApplicationStatus
from app.models.fit_score import FitGrade
from app.models.user_feedback import FeedbackAction
from app.schemas.fit_score import FitScoreOut

class JobPostingExtractionResult(BaseModel):
    company: Optional[str] = None
    title: str
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    experience_level: Optional[str] = None

# 지원상태 변경
class ApplicationStatusUpdate(BaseModel):
    application_status: ApplicationStatus

# Get /job-postings
# JobPosting/FitScore/UserFeedback 세 테이블을 조합한 결과
class JobPostingListItem(BaseModel):
    id: int
    company: Optional[str] = None
    title: str
    application_status: ApplicationStatus
    created_at: datetime

    fit_score: Optional[int] = None
    fit_grade: Optional[FitGrade] = None
    missing_skills_count: Optional[int] = None
    feedback: Optional[FeedbackAction] = None

# 상세(GET /job-postings/{id}) 응답.
class JobPostingDetailOut(BaseModel):
    id: int
    company: Optional[str] = None
    title: str
    url: str
    required_skills: List[str]
    preferred_skills: List[str]
    experience_level: Optional[str] = None
    source_site: Optional[str] = None
    application_status: ApplicationStatus
    created_at: datetime
    feedback: Optional[FeedbackAction] = None
    fit_score: Optional[FitScoreOut] = None