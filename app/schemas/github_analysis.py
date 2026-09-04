from typing import List, Optional

from pydantic import BaseModel, Field


class GithubAnalysisResult(BaseModel):
    languages: List[str] = Field(default_factory=list)
    readme_summary: Optional[str] = None
    verified_tech: List[str] = Field(default_factory=list)