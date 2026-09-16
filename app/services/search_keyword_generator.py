from typing import List

import anthropic
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.models.resume_profile import ResumeProfile

# LLM 호출용 전용 응답형. 중간결과
class SearchKeywordResult(BaseModel):
    keywords: List[str] = Field(default_factory=list, description="사람인/잡코리아 검색 키워드 목록")

# resume의 경력을 텍스트로 펼치는 로직
def _build_experience_context(resume: ResumeProfile) -> str:
    lines = []
    for item in resume.experience:
        description = item.get("description")
        if description:
            lines.append(f"- {item.get('company', '?')} ({item.get('period', '?')} - {item.get('role', '?')}: {description})")
    return "\n".join(lines)

# 활성화된 이력서의 키워드 목록 생성하여 반환
def generate_search_keywords(resume: ResumeProfile) -> List[str]:
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    experience_context = _build_experience_context(resume)

    prompt = (
        "다음은 한 지원자의 이력서 정보입니다. 이 정보를 보고 사람인/잡코리아에서 "
        "검색했을 때 이 지원자에게 맞는 채용공고를 최대한 놓치지 않고 찾아낼 수 있는 "
        "검색 키워드 목록을 만들어주세요.\n\n"
        "규칙:\n"
        "1. 기술 스택은 표기가 다를 수 있는 동의어도 함께 포함하세요 "
        "(예: React → React, 리액트 / Node.js → Node.js, 노드).\n"
        "2. 기술명 나열뿐 아니라, 경력을 참고해서 관련 직무명(예: 백엔드 개발자, "
        "서버 개발자)도 포함하세요.\n"
        "3. '개발자'처럼 너무 포괄적인 단어 하나만 있는 키워드는 만들지 마세요 — "
        "실제 채용 사이트에서 검색했을 때 관련도 높은 공고가 나올 정도로 구체적이어야 합니다.\n"
        "4. 10~15개 내외로 만들어주세요.\n\n"
        f"[보유 기술]\n{', '.join(resume.skills)}\n\n"
        f"[자기 신고 기술]\n{', '.join(resume.self_reported_tech)}\n\n"
        f"[경력]\n{experience_context or '경력 없음'}\n"
    )

    response = client.messages.parse(
        model="claude-sonnet-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
        output_format=SearchKeywordResult,
    )

    return response.parsed_output.keywords
