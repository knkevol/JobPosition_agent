import anthropic

from app.core.config import get_settings
from app.models.fit_score import FitGrade
from app.models.job_posting import JobPosting
from app.schemas.fit_score import FitScoreResult, FitScoreLLMResult

def _normalize(skill: str) -> str:
    return skill.strip().lower()

SELF_REPORTED_CONFIDENCE_WEIGHT = 0.6

# 사용자 보유 기술과 채용공고 요구 기술을 문자열 기준으로 비교하여 점수 산출
def compute_skill_match_rate(verified_skills: list[str], self_reported_skills: list[str], required_skills: list[str], preferred_skills: list[str]) -> float:
    normalized_verified = {_normalize(s) for s in verified_skills}
    normalized_self_reported = {_normalize(s) for s in self_reported_skills}

    # 기술 하나당 지원자의 신뢰점수 판정 로직
    def credit(skill: str) -> float:
        normalized = _normalize(skill)
        if normalized in normalized_verified:
            return 1.0
        if normalized in normalized_self_reported:
            return SELF_REPORTED_CONFIDENCE_WEIGHT
        return 0.0
    
    def match_rate(required: list[str]) -> float:
        if not required:
            return 100.0
        total_credit = sum(credit(skill) for skill in required)
        return (total_credit / len(required)) * 100

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
def calculate_fit_score(verified_skills: list[str], self_reported_skills: list[str], job_posting: JobPosting, base_score: float) -> FitScoreResult:
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    # base_score를 제공하여 기준점 근처에서 합리적으로 조정하도록 유도
    prompt = (
        "아래는 한 지원자가 보유한 기술 목록과, 특정 채용공고의 요건입니다.\n"
        "지원자 기술은 신뢰도가 다른 두 그룹으로 나뉘어 있습니다.\n"
        "- [GitHub로 검증된 기술]: 실제 저장소의 코드/의존성 파일에서 확인된 것 — 신뢰도 높음\n"
        "- [자기 신고 기술]: 이력서/포트폴리오에 본인이 적었지만 GitHub에서는 확인되지 않은 것 — "
        "실제로 쓸 줄 알 수도 있지만 과장/누락 가능성이 있음\n\n"
        "지원자 기술과 공고 요건을 의미 기준으로 비교해주세요 "
        "(예: 'React'와 '리액트', 'C++'와 'cpp'는 같은 기술로 취급).\n"
        "단, [GitHub로 검증된 기술]과 [자기 신고 기술] 양쪽에 표현만 다르고 의미상 같은 능력을 "
        "가리키는 항목이 있다면(예: 자기신고의 'UE Replication'과 검증된 기술의 'Replication/RPC "
        "(Net/UnrealNetwork)'는 같은 능력), 반드시 GitHub 검증 쪽으로만 취급해서 "
        "verified_matched_skills에 넣고, unverified_matched_skills에는 중복으로 넣지 마세요.\n\n"
        f"[GitHub로 검증된 기술]\n{', '.join(verified_skills) or '(없음)'}\n\n"
        f"[자기 신고 기술]\n{', '.join(self_reported_skills) or '(없음)'}\n\n"
        "[채용공고]\n"
        f"- 회사: {job_posting.company or '알 수 없음'}\n"
        f"- 직무: {job_posting.title}\n"
        f"- 필수기술: {', '.join(job_posting.required_skills) or '(명시 없음)'}\n"
        f"- 우대기술: {', '.join(job_posting.preferred_skills) or '(명시 없음)'}\n"
        f"- 경력요건: {job_posting.experience_level or '명시 없음'}\n\n"
        f"참고용 기준 점수(기계적 계산값, GitHub 검증 여부 가중치가 이미 반영됨): {base_score}/100\n"
        "이 기준 점수를 참고하되, 의미상 같은 기술인데 표기만 달라 놓친 일치가 있다면 "
        "직접 판단해서 반영해주세요.\n\n"
        "다음을 산출해주세요:\n"
        "1. verified_matched_skills: 공고 요구 기술 중 [GitHub로 검증된 기술]로 충족되는 것\n"
        "2. unverified_matched_skills: 공고 요구 기술 중 [자기 신고 기술]에만 있고 GitHub로는 "
        "확인 안 되는 것\n"
        "3. missing_skills: 공고에서 요구하지만 지원자에게 전혀 없는 기술\n"
        "4. reason: 지원 추천/비추천 이유를 2~3문장으로 설명. 자기 신고만 되어있고 GitHub로 "
        "검증되지 않은 기술이 점수에 영향을 줬다면 그 점도 언급해주세요.\n"
        "5. score: 0~100 사이의 최종 적합도 점수\n"
    )

    response = client.messages.parse(
        model="claude-sonnet-5",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
        output_format=FitScoreLLMResult,
    )

    llm_result = response.parsed_output
    matched_skills = list(dict.fromkeys(llm_result.verified_matched_skills + llm_result.unverified_matched_skills))

    return FitScoreResult(
        score=llm_result.score,
        matched_skills=matched_skills,
        verified_matched_skills=llm_result.verified_matched_skills,
        unverified_matched_skills=llm_result.unverified_matched_skills,
        missing_skills=llm_result.missing_skills,
        reason=llm_result.reason,
        grade=determine_grade(llm_result.score),
    )