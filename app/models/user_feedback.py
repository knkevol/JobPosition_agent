import enum

from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class FeedbackAction(str, enum.Enum):
    INTERESTED = "interested"
    EXCLUDED = "excluded" 

class UserFeedback(Base):
    __tablename__ = "user_feedbacks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False, index=True)

    action = Column(SAEnum(FeedbackAction, name="feedback_action"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="feedbacks")
    job_posting = relationship("JobPosting", back_populates="feedbacks")