from typing import List, Optional
from pydantic import BaseModel, Field

class ExperienceItem(BaseModel):
    company: str = Field(..., description="회사명")
    period: str = Field(..., description="근무 기간")
    role: str = Field(..., description="담당 직무")

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