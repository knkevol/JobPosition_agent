from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func

from app.core.database import Base

# 마지막으로 검색 키워드를 생성했을 때 기준이 된 이력서/포트폴리오 버전을 같이 저장
# 데일리 매칭 에이전트가 이 값과 지금 활성화된 이력서/포트폴리오를 비교해서, 동일하면 keywords를 그대로 재사용
class SearchKeywordCache(Base):
    __tablename__ = "search_keyword_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    resume_id = Column(Integer, ForeignKey("resume_profiles.id", ondelete="SET NULL"), nullable=True)
    portfolio_version_id = Column(Integer, ForeignKey("portfolio_versions.id", ondelete="SET NULL"), nullable=True)
    last_liked_feedback_id = Column(Integer, nullable=True)

    keywords = Column(ARRAY(String), nullable=False, server_default="{}")
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)