from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict

# LLM이 README + 의존성 파일 + 소스코드를 읽고 판단하여 채우는 스키마
class GithubLLMAnalysis(BaseModel):
    readme_summary: Optional[str] = Field(
        default=None, description="README 기반 프로젝트 핵심 기능 요약"
    )
    verified_tech: List[str] = Field(default_factory=list)

# languages + LLM 분석 결과를 합친 최종 형태(DB저장 직전)
class GithubAnalysisResult(GithubLLMAnalysis):
    languages: List[str] = Field(default_factory=list)

# GET 엔드포인트 응답용
class GithubRepoAnalysisOut(BaseModel):
    id: int
    portfolio_project_id: int
    repo_url: str
    languages: List[str]
    readme_summary: Optional[str] = None
    verified_tech: List[str]
    analyzed_at: datetime

    model_config = ConfigDict(from_attributes=True)