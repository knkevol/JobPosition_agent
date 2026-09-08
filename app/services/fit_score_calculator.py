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
def calculate_fit_score(verified_skills: list[str], self_reported_skills: list[str], job_posting: JobPosting, base_score: float, experience_context: str = "") -> FitScoreResult:
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
        f"[경력 설명 — 이력서 원문 기반, 기술 목록에 안 담기는 업무/협업 경험]\n"
        f"{experience_context or '(없음)'}\n"
        "경력 설명은 협업/커뮤니케이션 경험, 도메인 지식처럼 GitHub 저장소로는 애초에 "
        "확인할 방법이 없는 성격의 정보입니다. 위 [자기 신고 기술]과는 달라서, "
        "'GitHub로 검증이 안 됐으니 신뢰도가 낮다'는 논리를 여기에 적용하지 마세요. "
        "이력서에 적힌 내용을 그대로 사실로 받아들여 판단 근거로 사용하세요. 경력 설명으로 "
        "충족되는 공고 요건이 있다면 missing_skills에는 넣지 마세요. 단, 절대 그냥 "
        "빠뜨리지 말고 reason에서 '~요건은 경력 설명의 ~ 내용으로 충족됨'처럼 어떤 요건이 "
        "어떤 근거로 충족됐는지 반드시 명시적으로 언급하세요 — 언급 없이 누락되는 요건이 "
        "있으면 안 됩니다. 여기서 확인된 내용을 기술 매칭 목록(verified/"
        "unverified_matched_skills)에 억지로 넣지는 마세요.\n\n"
        "[채용공고]\n"
        f"- 회사: {job_posting.company or '알 수 없음'}\n"
        f"- 직무: {job_posting.title}\n"
        f"- 필수기술: {', '.join(job_posting.required_skills) or '(명시 없음)'}\n"
        f"- 우대기술: {', '.join(job_posting.preferred_skills) or '(명시 없음)'}\n"
        f"- 경력요건: {job_posting.experience_level or '명시 없음'}\n\n"
        f"참고용 기준 점수(기계적 계산값): {base_score}/100\n"
        "주의: 이 기준 점수는 완전 문자열 일치만 확인하는 단순 계산이라, 표현이 조금만 달라도 "
        "매칭을 놓쳐 실제보다 낮게(0에 가깝게) 나오는 경우가 많습니다. 이 숫자 자체를 신뢰하지 "
        "말고 참고만 하되, 최종 판단은 위 기술 목록을 의미 기준으로 직접 비교해서 내려주세요.\n\n"
        "다음을 산출해주세요:\n"
        "1. verified_matched_skills: 공고 요구 기술 중 [GitHub로 검증된 기술]로 충족되는 것\n"
        "2. unverified_matched_skills: 공고 요구 기술 중 [자기 신고 기술]에만 있고 GitHub로는 "
        "확인 안 되는 것\n"
        "3. missing_skills: 공고에서 요구하지만 지원자에게 전혀 없는 기술\n"
        "4. reason: 지원 추천/비추천 이유를 2~3문장으로 설명. 자기 신고만 되어있고 GitHub로 "
        "검증되지 않은 기술이 점수에 영향을 줬다면 그 점도 언급해주세요.\n"
        "5. score: 0~100 사이의 최종 적합도 점수. reason에서 설명한 근거의 강도와 반드시 "
        "일관되게 매겨주세요 — 예를 들어 reason에서 '소폭 영향'이라고 썼다면 점수도 그에 맞게 "
        "소폭만 조정하고, reason과 점수 변화폭이 서로 어긋나지 않도록 하세요.\n"
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