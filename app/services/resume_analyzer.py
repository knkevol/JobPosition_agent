import anthropic

from app.core.config import get_settings
from app.schemas.resume import ResumeExtractionResult

# pdf 텍스트를 Claude API로 보냄
def analyze_resume_text(resume_text: str) -> ResumeExtractionResult:
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    response = client.messages.parse(
        model="claude-sonnet-5",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": (
                "다음은 한 사람의 이력서 텍스트입니다. 기술 스택, 경력(회사/기간/역할), "
                "학력, 본인이 사용 가능하다고 밝힌 기술을 구조화해서 추출해주세요.\n\n"
                "경력(experience) 항목의 description에는 단순 직함(role)에 담기지 않는 "
                "내용 — 주요 업무, 비개발자 직군과의 협업/커뮤니케이션 경험, 사용 기술, "
                "성과 등 — 을 이력서 원문에 있는 그대로(과장하지 말고) 서술형으로 담아주세요. "
                "원문에 해당 내용이 없으면 description은 비워두세요.\n\n"
                f"{resume_text}"
            ),
        }],
        # output_format에 맞춰 SDK가 클래스 모양의 JSON을 강제하고 응답이 오면 반환형으로 변환 및 검증
        output_format=ResumeExtractionResult,
    )

    return response.parsed_output