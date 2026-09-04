from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base

class ResumeProfile(Base):
    __tablename__ = "resume_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # ForeignKey : 참조무결성
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # 예: ["Python", "C++", "Unreal Engine"]
    skills = Column(ARRAY(String), nullable=False, server_default="{}")
    experience = Column(JSONB, nullable=False, server_default="[]")
    education = Column(JSONB, nullable=False, server_default="[]")

    self_repoted_tech = Column(ARRAY(String), nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user = relationship("User", back_populates="resume_profiles")