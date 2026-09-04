from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class GithubRepoAnalysis(Base):
    __tablename__ = "github_repo_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)

    portfolio_project_id = Column(
        Integer, ForeignKey("portfolio_projects.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    repo_url = Column(String(500), nullable=False)
    languages = Column(ARRAY(String), nullable=False, server_default="{}")
    readme_summary = Column(Text, nullable=True)

    # GitHub에서 실제로 확인된 기술 목록 - self_reported_tech와 비교가 핵심
    verified_tech = Column(ARRAY(String), nullable=False, server_default="{}")

    analyzed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    portfolio_project = relationship("PortfolioProject", back_populates="github_analysis")