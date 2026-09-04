from typing import List, Optional

from pydantic import BaseModel, Field

class PortfolioProjectExtraction(BaseModel):
    title: str
    description: Optional[str] = None
    tech_stack: List[str] = Field(default_factory=list)
    github_url: Optional[str] = None

class PortfolioExtractionResult(BaseModel):
    projects: List[PortfolioProjectExtraction] = Field(default_factory=list)