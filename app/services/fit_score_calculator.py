import anthropic

from app.core.config import get_settings
from app.models.fit_score import FitGrade
from app.models.job_posting import JobPosting
from app.schemas.fit_score import FitScoreResult

def _normalize(skill: str) -> str:
    return skill.strip().lower()

# 사용자 보유 기술과 채용공고 요구 기술을 문자열 기준으로 비교하여 점수 산출
def compute_skill_match_rate(user_skills: list[str], required_skills: list[str], preferred_skills: list[str]) -> float:
    normalized_user = {_normalize(s) for s in user_skills}

    def match_rate(required: list[str]) -> float:
        if not required:
            return 100.0

        # required에 있는 기술 중 normalized_user에도 포함된 기술의 개수를 세어서 matched에 저장
        matched = sum(1 for skill in required if _normalize(skill) in normalized_user)
        return (matched / len(required)) * 100

    required_rate = match_rate(required_skills)
    preferred_rate = match_rate(preferred_skills)

    # 필수 기술 일치율 70% + 우대기술 일치율 30% 의 가중치를 둔다.
    return round(required_rate * 0.7 + preferred_rate * 0.3, 1)

def determine_grade(score: int) -> FitGrade:
    if score >= 85:
        return FitGrade.STRONG_RECOMMEND
    if score >= 65:
        return FitGrade.RECOMMEND
    if score >= 45:
        return FitGrade.REVIEW
    return FitGrade.NOT_RECOMMEND

# 사용자 역량 + 채용공고를 LLM에 전달하여 정성적 비교
def calculate_fit_score(user_skills: list[str], job_posting: JobPosting, base_score: float) -> FitScoreResult:
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    # base_score를 제공하여 기준점 근처에서 합리적으로 조정하도록 유도
    prompt = (
        "아래는 한 지원자가 보유한 기술 목록과, 특정 채용공고의 요건입니다.\n"
        "지원자 기술과 공고 요건을 의미 기준으로 비교해주세요 "
        "(예: 'React'와 '리액트', 'C++'와 'cpp'는 같은 기술로 취급).\n\n"
        f"[지원자 보유 기술]\n{', '.join(user_skills) or '(없음)'}\n\n"
        "[채용공고]\n"
        f"- 회사: {job_posting.company or '알 수 없음'}\n"
        f"- 직무: {job_posting.title}\n"
        f"- 필수기술: {', '.join(job_posting.required_skills) or '(명시 없음)'}\n"
        f"- 우대기술: {', '.join(job_posting.preferred_skills) or '(명시 없음)'}\n"
        f"- 경력요건: {job_posting.experience_level or '명시 없음'}\n\n"
        f"참고용 기준 점수(문자열 완전일치 기준 기계적 계산값): {base_score}/100\n"
        "이 기준 점수를 참고하되, 의미상 같은 기술인데 표기만 달라 놓친 일치가 있다면 "
        "직접 판단해서 반영해주세요.\n\n"
        "다음을 산출해주세요:\n"
        "1. matched_skills: 지원자가 실제로 충족하는 공고 요구 기술 목록\n"
        "2. missing_skills: 공고에서 요구하지만 지원자에게 없는 기술 목록\n"
        "3. reason: 이 공고에 지원을 추천/비추천하는 이유를 2~3문장으로 설명\n"
        "4. score: 0~100 사이의 최종 적합도 점수\n"
    )

    response = client.messages.parse(
        model="claude-sonnet-5",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
        output_format=FitScoreResult,
    )

    result = response.parsed_output
    result.grade = determine_grade(result.score)
    return result