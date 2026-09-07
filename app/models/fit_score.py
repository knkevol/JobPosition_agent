import enum

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base

class FitGrade(str, enum.Enum):
    STRONG_RECOMMEND = "strong_recommend"  # 강력추천
    RECOMMEND = "recommend"                # 추천
    REVIEW = "review"                      # 검토
    NOT_RECOMMEND = "not_recommend"        # 비추천

class FitScore(Base):
    __tablename__ = "fit_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False, index=True)

    score = Column(Integer, nullable=False)
    matched_skills = Column(ARRAY(String), nullable=False, server_default="{}")
    verified_matched_skills = Column(ARRAY(String), nullable=False, server_default="{}")
    unverified_matched_skills = Column(ARRAY(String), nullable=False, server_default="{}")
    missing_skills = Column(ARRAY(String), nullable=False, server_default="{}")
    reason = Column(Text, nullable=True)

    # SAEnum : 파이썬 Enum을 DB의 진짜 ENUM 타입으로 매핑.
    grade = Column(SAEnum(FitGrade, name="fit_grade"), nullable=False)

    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="fit_scores")
    job_posting = relationship("JobPosting", back_populates="fit_scores")