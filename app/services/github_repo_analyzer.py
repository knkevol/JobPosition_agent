import anthropic

from app.core.config import get_settings
from app.schemas.github_analysis import GithubLLMAnalysis, RelevantFilePaths, ClaimVerificationResult

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

# --- 사용자 주장 검증 로직(수동 기능 추가) ---
# 경로를 보고 기능이 구현되어 있을 것 같은 파일 추측
def select_relevant_file_paths(claim: str, all_paths: list[str], max_paths: int = 8) -> list[str]:
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    paths_text = "\n".join(all_paths)

    response = client.messages.parse(
        model="claude-sonnet-5",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": (
                "다음은 한 GitHub 저장소의 소스 파일 경로 목록입니다. 파일 내용은 아직 안 보여줬고, "
                "경로(폴더/파일명)만 보고 판단해야 합니다.\n\n"
                f"[사용자 주장]\n{claim}\n\n"
                f"[파일 경로 목록]\n{paths_text}\n\n"
                f"이 주장을 검증하려면 어떤 파일들을 실제로 열어봐야 할지, 관련성이 높은 순서로 "
                f"최대 {max_paths}개까지 골라주세요. 경로 이름에서 유추 가능한 관련성만 근거로 삼고, "
                "관련 있어 보이는 파일이 없으면 빈 목록을 반환하세요."
            ),
        }],
        output_format=RelevantFilePaths,
    )
    return response.parsed_output.paths[:max_paths]

# 분류된 파일들의 내용을 보고 근거가 있는지 최종 판단
def verify_user_claim(claim: str, file_contents: dict[str, str]) -> ClaimVerificationResult:
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    files_text = "\n\n".join(f"[{path}]\n{content}" for path, content in file_contents.items()) or "(없음)"

    response = client.messages.parse(
        model="claude-sonnet-5",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": (
                "아래는 사용자가 '직접 구현했다'고 주장하는 기능과, 그 근거를 확인하기 위해 "
                "열어본 실제 소스코드입니다.\n\n"
                f"[사용자 주장]\n{claim}\n\n"
                f"[확인한 소스코드]\n{files_text}\n\n"
                "이 코드에서 주장을 뒷받침하는 근거를 찾을 수 있는지 판단해주세요.\n"
                "- found: 근거를 찾았으면 true, 못 찾았으면 false\n"
                "- tech_label: found가 true라면, 이 기능을 짧은 기술 이름으로 뭐라고 부를지 "
                "(예: 'Listen Server (Authority 기반 네트워크 구조)')\n"
                "- evidence: 근거가 된 파일 경로와, 그 파일의 어떤 부분이 왜 근거가 되는지 설명\n"
                "- explanation: 종합적인 판단 이유 (근거가 부족하면 왜 부족한지도 명시)\n"
                "추측하지 말고, 코드에 실제로 있는 내용만 근거로 삼으세요."
            ),
        }],
        output_format=ClaimVerificationResult,
    )
    return response.parsed_output

# README 기반 자동 분석용 : README가 없을 시 fetch_source_snippets으로 대체
def select_paths_from_readme(readme: str, all_paths: list[str], max_paths: int = 8) -> list[str]:
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    paths_text = "\n".join(all_paths)
    response = client.messages.parse(
        model="claude-sonnet-5",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": (
                "다음은 한 GitHub 저장소의 README와, 그 저장소의 전체 소스 파일 경로 목록입니다. "
                "파일 내용은 아직 안 보여줬고, 경로(폴더/파일명)만 보고 판단해야 합니다.\n\n"
                f"[README]\n{readme}\n\n"
                f"[파일 경로 목록]\n{paths_text}\n\n"
                f"README에서 설명하는 주요 기능들이 실제로 구현되어 있을 가능성이 높은 파일을, "
                f"경로 이름에서 유추해서 최대 {max_paths}개까지 골라주세요. 파일 크기는 신경 쓰지 "
                "말고, README 내용과의 관련성만 기준으로 삼으세요."
            ),
        }],
        output_format=RelevantFilePaths,
    )
    return response.parsed_output.paths[:max_paths]

