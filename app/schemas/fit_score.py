from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from app.models.fit_score import FitGrade


class FitScoreResult(BaseModel):
    # ge=0, le=100: "Greater or Equal(이상) 0, Less or Equal(이하) 100" - 0~100 범위를 벗어나면 검증 실패
    score: int = Field(..., ge=0, le=100, description="0~100 사이의 적합도 점수")
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    reason: Optional[str] = None
    grade: FitGrade

class FitScoreOut(BaseModel):
    id: int
    user_id: int
    job_id: int
    score: int
    matched_skills: List[str]
    missing_skills: List[str]
    reason: Optional[str] = None
    grade: FitGrade
    calculated_at: datetime

    model_config = ConfigDict(from_attributes=True)