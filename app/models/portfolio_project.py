from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base

class PortfolioProject(Base):
    __tablename__ = "portfolio_projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    # Text : String과 달리 길이 제한 없음
    description = Column(Text, nullable=True)
    tech_stack = Column(ARRAY(String), nullable=False, server_default="{}")
    github_url = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="portfolio_projects")

    # GitHub 분석 결과 : relationship (1:1 관계)
    github_analysis = relationship(
        "GithubRepoAnalysis", back_populates="portfolio_project", uselist=False, cascade="all, delete-orphan"
    )