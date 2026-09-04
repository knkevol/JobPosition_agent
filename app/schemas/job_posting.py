from typing import List, Optional

from pydantic import BaseModel, Field

class JobPostingExtractionResult(BaseModel):
    company: Optional[str] = None
    title: str
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    experience_level: Optional[str] = None