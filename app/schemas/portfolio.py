from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict

class PortfolioProjectExtraction(BaseModel):
    title: str
    description: Optional[str] = None
    tech_stack: List[str] = Field(default_factory=list)
    github_url: Optional[str] = None

class PortfolioExtractionResult(BaseModel):
    projects: List[PortfolioProjectExtraction] = Field(default_factory=list)

# DB에 저장된 프로젝트 1개를 그대로 반환할 때 쓰는 스키마.
# PortfolioProjectExtraction과 필드는 같지만, id/created_at처럼 DB에만 있는값까지 포함해야 해서 별도로 둔다.
class PortfolioProjectOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    tech_stack: List[str]
    github_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# 버전(=업로드 한 번) 단위 응답. 이 버전에 속한 프로젝트 전체를 함께 내려준다.
class PortfolioVersionOut(BaseModel):
    id: int
    user_id: int
    is_saved: bool
    is_active: bool
    label: Optional[str] = None
    created_at: datetime
    projects: List[PortfolioProjectOut]

    model_config = ConfigDict(from_attributes=True)