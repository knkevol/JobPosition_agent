import anthropic

from app.core.config import get_settings
from app.schemas.github_analysis import GithubLLMAnalysis

# fetcher가 모아온 자료를 넘겨 "실제로 검증된 기술"+"README 요약"만 구조화하여 돌려받음
def analyze_github_repository(readme: str | None, dependency_manifests: dict[str, str], source_snippets: dict[str, str]) -> GithubLLMAnalysis:
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    manifests_text = "\n\n".join(f"[{path}]\n{content}" for path, content in dependency_manifests.items()) or "(없음)"
    snippets_text = "\n\n".join(f"[{path}]\n{content}" for path, content in source_snippets.items()) or "(없음)"

    response = client.messages.parse(
        model="claude-sonnet-5",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": (
                "다음은 GitHub 저장소 하나에서 가져온 자료입니다. README, 의존성/패키지 "
                "정의 파일, 실제 소스 코드 일부가 순서대로 주어집니다. 이 자료만 근거로 "
                "삼아 다음 두 가지를 작성해주세요.\n"
                "1. readme_summary: 이 프로젝트의 목적과 핵심 기능을 2~3문장으로 요약\n"
                "2. verified_tech: README의 설명이 아니라 의존성 파일과 실제 코드에서 "
                "'확인되는' 기술/라이브러리/프레임워크 이름만 나열하세요. "
                "README에만 언급되고 코드/의존성에서 근거를 찾을 수 없는 항목은 제외합니다.\n\n"
                f"[README]\n{readme or '(README 없음)'}\n\n"
                f"[의존성 파일]\n{manifests_text}\n\n"
                f"[주요 소스 코드]\n{snippets_text}"
            ),
        }],

        # SDK가 GithubLlmAnalysis 모양의 JSON을 강제, 해당 타입으로 검증/변환해서 반환
        output_format=GithubLLMAnalysis,
    )

    return response.parsed_output