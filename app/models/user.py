from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base

class User(Base):
    # 실제 DB에서의 테이블 이름 설정
    __tablename__ = "users"

    # 테이블의 컬럼 하나 정의
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)

    email = Column(String(255), nullable=False, unique=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False) # func.now() : 현재 시각
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False) # onupdate : row 수정 시마다 시간 업데이트

    # relationship : 파이썬에서 user와 연결된 것들을 편하게 조회하기 위한 속성 
    # ex) user.resume_profiles => 목록 자동 조회
    resume_profiles = relationship("ResumeProfile", back_populates="user", cascade="all, delete-orphan")
    portfolio_projects = relationship("PortfolioProject", back_populates="user", cascade="all, delete-orphan")
    job_positngs = relationship("JobPosting", back_populates="user", cascade="all, delete-orphan")
    fit_scores = relationship("FitScore", back_populates="user", cascade="all, delete-orphan")
    feedbacks = relationship("UserFeedback", back_populates="user", cascade="all, delete-orphan")
