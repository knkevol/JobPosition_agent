import anthropic

from app.core.config import get_settings
from app.schemas.resume import ResumeExtractionResult

# pdf 텍스트 -> Claude API
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
                f"{resume_text}"
            ),
        }],
        # output_format에 맞춰 SDK가 클래스 모양의 JSON을 강제하고 응답이 오면 반환형으로 변환 및 검증
        output_format=ResumeExtractionResult,
    )

    return response.parsed_output