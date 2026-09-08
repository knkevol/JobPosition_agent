import enum

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base

class ApplicationStatus(str, enum.Enum):
    NOT_APPLIED = "not_applied" # 미지원
    APPLIED = "applied"         # 지원완료


class JobPosting(Base):
    __tablename__ = "job_postings"

    # 같은 사용자가 같은 URL을 두 번 분석 요청해도 중복 행이 쌓이지 않도록
    # (user_id, url) 조합 항상 유일 제약 추가
    __table_args__ = (
        UniqueConstraint("user_id", "url", name="uq_job_postings_user_url"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    company = Column(String(255), nullable=True)
    title = Column(String(255), nullable=False)
    url = Column(String(1000), nullable=False)

    required_skills = Column(ARRAY(String), nullable=False, server_default="{}")
    preferred_skills = Column(ARRAY(String), nullable=False, server_default="{}")
    experience_level = Column(String(100), nullable=True)  # 예: 신입, 3년 이상
    source_site = Column(String(50), nullable=True)        # 예: 사람인, 잡코리아

    application_status = Column(SAEnum(ApplicationStatus, name="application_status"), nullable=False, server_default=ApplicationStatus.NOT_APPLIED.name)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="job_postings")
    fit_scores = relationship("FitScore", back_populates="job_posting", cascade="all, delete-orphan")
    feedbacks = relationship("UserFeedback", back_populates="job_posting", cascade="all, delete-orphan")