from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.user_feedback import FeedbackAction

# 피드백을 남길 때 클라이언트가 보내는 요청
class FeedbackRequest(BaseModel):
    action: FeedbackAction

# 저장된 피드백 이벤트를 그대로 응답으로 돌려주는 형태
class FeedbackOut(BaseModel):
    id: int
    job_id: int
    action: FeedbackAction
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)