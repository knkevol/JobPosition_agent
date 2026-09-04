import anthropic

from app.core.config import get_settings
from app.schemas.job_posting import JobPostingExtractionResult

def analyze_job_posting_text(posting_text: str) -> JobPostingExtractionResult:
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    response = client.messages.parse(
        model="claude-sonnet-5",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": (
                "다음은 채용공고 페이지에서 가져온 텍스트입니다. 회사명, 직무명, "
                "필수기술, 우대사항, 경력요건을 구조화해서 추출해주세요. "
                "메뉴/광고/추천공고 등 채용공고와 무관한 텍스트는 무시하세요.\n\n"
                f"{posting_text}"
            ),
        }],
        output_format=JobPostingExtractionResult,
    )

    return response.parsed_output