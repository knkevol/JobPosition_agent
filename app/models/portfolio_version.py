from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base

class PortfolioVersion(Base):
    __tablename__ = "portfolio_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    is_saved = Column(Boolean, nullable=False, server_default="false")
    is_active = Column(Boolean, nullable=False, server_default="false")
    label = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="portfolio_versions")
    # cascade="all, delete-orphan": 버전이 지워지면 속한 프로젝트도 같이 정리
    projects = relationship(
        "PortfolioProject",
        back_populates="portfolio_version",
        cascade="all, delete-orphan",
        order_by="PortfolioProject.id",
    )