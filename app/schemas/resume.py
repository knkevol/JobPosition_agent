from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class ExperienceItem(BaseModel):
    company: str = Field(..., description="회사명")
    period: str = Field(..., description="근무 기간")
    role: str = Field(..., description="담당 직무")
    description: Optional[str] = Field(None, description="주요 업무 내용, 사용 기술 및 성과 등 자유 서술")

class EducationItem(BaseModel):
    school: str
    degree: Optional[str] = None
    period: Optional[str] = None

# PDF 분석 후 돌려주는 형태
class ResumeExtractionResult(BaseModel):
    skills: List[str] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    self_reported_tech: List[str] = Field(default_factory=list)

class ResumeProfileUpdate(BaseModel):
    skills: Optional[List[str]] = None
    experience: Optional[List[ExperienceItem]] = None
    education: Optional[List[EducationItem]] = None
    self_reported_tech: Optional[List[str]] = None

# SQLAlchemy 객체(ResumePRofile)를 이 클래스대로 변환해서 응답
class ResumeProfileOut(BaseModel):
    id: int
    user_id: int
    skills: List[str]
    experience: List[ExperienceItem]
    education: List[EducationItem]
    self_reported_tech: List[str]
    created_at: datetime

    # ResumeProfile 객체를 dict로 변환 가능
    model_config = ConfigDict(from_attributes=True)
