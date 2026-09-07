import anthropic

from app.core.config import get_settings
from app.schemas.portfolio import PortfolioExtractionResult

def analyze_portfolio_text(portfolio_text: str) -> PortfolioExtractionResult:
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    response = client.messages.parse(
         model="claude-sonnet-5",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": (
                "다음은 한 사람의 포트폴리오 텍스트입니다. 포트폴리오에 소개된 "
                "프로젝트들을 하나씩 구분하여, 각 프로젝트의 제목(title), 설명(description), "
                "사용 기술 스택(tech_stack), 그리고 GitHub Repository URL(github_url, 있는 경우만)을 "
                "추출해주세요.\n"
                "GitHub URL을 찾을 때는 본문에 적힌 화면 텍스트가 중간에 잘려 있을 수 있으니, "
                "텍스트 마지막의 '[문서에 포함된 실제 하이퍼링크 목록]'에 나온 완전한 주소를 "
                "우선적으로 사용하세요. 브랜치 경로(/tree/<branch>, /blob/<branch>/...)가 붙어 "
                "있다면 지우지 말고 그대로 유지하세요.\n"
                "만약 같은 프로젝트를 설명하는 문단에 GitHub 링크가 여러 개 등장하면(예: 브랜치별 "
                "데모 영상 링크), 링크 개수만큼 프로젝트 항목을 각각 따로 만들어서 반환하세요. "
                "이때 title은 '프로젝트명 (구분자)' 형태로 구분해주세요. 예: 'Rendering Engine "
                "(fps)', 'Rendering Engine (gpu)'.\n"
                "명시되지 않은 프로젝트는 null로 두세요.\n\n"
                f"{portfolio_text}"
            ),
        }],
        output_format=PortfolioExtractionResult,
    )

    return response.parsed_output