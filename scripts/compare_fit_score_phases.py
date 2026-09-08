import json
import sys
from pathlib import Path

# Path(__file__): 이 스크립트 파일 자신의 경로 -> resolve()로 절대경로 변환
# 프로젝트 루트를 sys.path에 넣어서 app.* 모듈을 import할 수 있게 함
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import anthropic
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.job_posting import JobPosting
from app.models.fit_score import FitGrade
from app.services.fit_score_calculator import (
    compute_skill_match_rate,
    determine_grade,
    calculate_fit_score,
)
from app.services.user_service import get_or_create_default_user
# fit_scores 라우터 안에 있는 "이력서+포트폴리오+GitHub 검증 결과 수집" 로직을 그대로 재사용.
# 앞에 _가 붙은 이름이라도 파이썬에서는 그냥 함수라서 import해서 쓸 수 있음 (강제 private 아님).
from app.api.routes.fit_scores import _collect_user_skills

BASE_DIR = Path(__file__).resolve().parent.parent / "test_data"
CACHE_PHASE3_DIR = BASE_DIR / "chache" / "fit_score_phase3"
CACHE_PHASE5_DIR = BASE_DIR / "chache" / "fit_score_phase5"
CACHE_PHASE3_DIR.mkdir(parents=True, exist_ok=True)
CACHE_PHASE5_DIR.mkdir(parents=True, exist_ok=True)


# Phase 3 시절에는 LLM 결과 스키마에 grade 필드까지 포함해서 그대로 파싱했었음 (지금은 FitScoreResult가
# verified/unverified로 나뉘어 더 이상 이 모양이 아니라서, 베이스라인 재현용으로 그때 스키마를 그대로 복원)
class _Phase3LLMResult(BaseModel):
    score: int = Field(..., ge=0, le=100)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    reason: str | None = None
    grade: FitGrade | None = None  # LLM에게는 요청하지만 실제 등급은 determine_grade()로 다시 계산해서 덮어씀


# --- 아래 두 함수는 커밋 658b716(Phase 3) 시절 fit_score_calculator.py를 그대로 재현한 것.
# 운영 코드(app/services/fit_score_calculator.py)는 이미 Phase 5로 대체되어 이 버전이 안 남아있기 때문에,
# "GitHub 검증 반영 전에는 점수가 어떻게 나왔는지" 재현하려고 검증 스크립트 안에만 복원해둠.
def _phase3_match_rate(user_skills: list[str], required_skills: list[str], preferred_skills: list[str]) -> float:
    normalized_user = {s.strip().lower() for s in user_skills}

    def match_rate(required: list[str]) -> float:
        if not required:
            return 100.0
        matched = sum(1 for skill in required if skill.strip().lower() in normalized_user)
        return (matched / len(required)) * 100

    required_rate = match_rate(required_skills)
    preferred_rate = match_rate(preferred_skills)
    return round(required_rate * 0.7 + preferred_rate * 0.3, 1)


def _phase3_calculate_fit_score(user_skills: list[str], job_posting: JobPosting, base_score: float) -> _Phase3LLMResult:
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    # Phase 3 원본 프롬프트 그대로: 자기신고/GitHub검증 구분 없이 "지원자 보유 기술" 한 덩어리로만 비교
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
        output_format=_Phase3LLMResult,
    )
    result = response.parsed_output
    result.grade = determine_grade(result.score)
    return result


def _get_phase3_result(job_posting: JobPosting, user_skills: list[str]) -> _Phase3LLMResult:
    cache_path = CACHE_PHASE3_DIR / f"{job_posting.id}.json"
    if cache_path.exists():
        with open(cache_path, "r", encoding="utf-8") as f:
            return _Phase3LLMResult.model_validate(json.load(f))

    base_score = _phase3_match_rate(user_skills, job_posting.required_skills, job_posting.preferred_skills)
    result = _phase3_calculate_fit_score(user_skills, job_posting, base_score)

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)
    return result


def _get_phase5_result(job_posting: JobPosting, verified_skills: list[str], self_reported_skills: list[str], experience_context: str):
    cache_path = CACHE_PHASE5_DIR / f"{job_posting.id}.json"
    from app.schemas.fit_score import FitScoreResult

    if cache_path.exists():
        with open(cache_path, "r", encoding="utf-8") as f:
            return FitScoreResult.model_validate(json.load(f))

    base_score = compute_skill_match_rate(
        verified_skills=verified_skills,
        self_reported_skills=self_reported_skills,
        required_skills=job_posting.required_skills,
        preferred_skills=job_posting.preferred_skills,
    )
    result = calculate_fit_score(verified_skills, self_reported_skills, job_posting, base_score, experience_context)

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)
    return result


def main():
    db = SessionLocal()
    try:
        user = get_or_create_default_user(db)
        job_postings = db.query(JobPosting).filter(JobPosting.user_id == user.id).order_by(JobPosting.id).all()

        if not job_postings:
            print("분석된 채용공고가 없습니다. 먼저 /job-postings/analyze로 공고를 분석해주세요.")
            return

        try:
            self_reported_skills, verified_skills, experience_context = _collect_user_skills(db, user.id)
        except Exception as e:
            print(f"사용자 역량 데이터를 불러오지 못했습니다: {e}")
            print("먼저 이력서를 업로드/분석해주세요.")
            return

        # Phase 3는 검증 구분이 없었으므로, 두 목록을 합쳐 하나의 "보유 기술" 집합으로 취급 (중복 제거)
        phase3_user_skills = list(dict.fromkeys(self_reported_skills + verified_skills))

        score_diffs = []
        grade_changes = 0

        for job in job_postings:
            phase3 = _get_phase3_result(job, phase3_user_skills)
            phase5 = _get_phase5_result(job, verified_skills, self_reported_skills, experience_context)

            # LLM 재호출 없이 기계적 base_score만 다시 계산해서, 점수 하락이
            # "계산식(가중치)" 때문인지 "LLM의 정성적 판단" 때문인지 구분한다
            phase3_base = _phase3_match_rate(phase3_user_skills, job.required_skills, job.preferred_skills)
            phase5_base = compute_skill_match_rate(
                verified_skills=verified_skills,
                self_reported_skills=self_reported_skills,
                required_skills=job.required_skills,
                preferred_skills=job.preferred_skills,
            )
            print(f"  [진단] base_score: phase3={phase3_base}  phase5={phase5_base}  (base 차이={phase5_base - phase3_base:+.1f})")
            print(f"  [진단] LLM 조정폭: phase3={phase3.score - phase3_base:+.1f}  phase5={phase5.score - phase5_base:+.1f}")

            diff = phase5.score - phase3.score
            score_diffs.append(diff)
            if phase3.grade != phase5.grade:
                grade_changes += 1

            print(f"\n=== [{job.id}] {job.company or '회사 미상'} - {job.title} ===")
            print(f"Phase3 (GitHub 미반영): score={phase3.score:3d}  grade={phase3.grade.value}")
            print(f"  matched: {phase3.matched_skills}")
            print(f"  missing: {phase3.missing_skills}")
            print(f"Phase5 (GitHub 반영)  : score={phase5.score:3d}  grade={phase5.grade.value}")
            print(f"  검증됨(verified_matched): {phase5.verified_matched_skills}")
            print(f"  자기신고만(unverified_matched): {phase5.unverified_matched_skills}")
            print(f"  missing: {phase5.missing_skills}")
            arrow = "▲" if diff > 0 else ("▼" if diff < 0 else "-")
            print(f"점수 변화: {arrow} {diff:+d}점" + (f"  (등급 변경: {phase3.grade.value} → {phase5.grade.value})" if phase3.grade != phase5.grade else ""))

        avg_diff = sum(score_diffs) / len(score_diffs)
        print(f"\n===== 요약 ({len(job_postings)}개 공고) =====")
        print(f"평균 점수 변화(Phase5 - Phase3): {avg_diff:+.1f}점")
        print(f"등급이 달라진 공고 수: {grade_changes}개 / {len(job_postings)}개")
        print("\n※ '자기신고만(unverified_matched)' 항목이 있는데도 Phase5 점수가 Phase3와 거의 같다면,")
        print("   GitHub 검증 여부가 점수에 충분히 반영되지 않고 있다는 신호이니 가중치(SELF_REPORTED_CONFIDENCE_WEIGHT)를 재검토해야 합니다.")
    finally:
        db.close()


if __name__ == "__main__":
    main()