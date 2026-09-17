import logging
import sys
from datetime import date
from pathlib import Path

# 로그 설정을 다른 모든 import보다 앞에 둔다. app 관련 모듈 import가 실패해도
# (예: 스케줄러가 가상환경이 아닌 다른 파이썬으로 실행되어 패키지가 없는 경우)
# 그 실패 자체가 로그 파일에 남도록 하기 위함 — "로그가 아예 안 남는" 상황 자체를 없앤다.
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"daily_agent_{date.today().isoformat()}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),  # 콘솔(cmd 창)에도 동시 출력
    ],
)
logger = logging.getLogger(__name__)

try:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    from app.core.database import SessionLocal
    from app.models.job_posting import JobPosting
    from app.models.fit_score import FitScore, FitGrade
    from app.models.user_feedback import UserFeedback, FeedbackAction
    from app.services.user_service import get_or_create_default_user
    from app.services.search_keyword_service import get_search_keywords
    from app.services.job_search_fetcher import search_saramin, search_jobkorea
    from app.services.job_posting_service import analyze_or_get_existing, NotRelevantError, ExcludedByKeywordError
    from app.services.fit_score_service import calculate_and_save_fitscore, collect_user_skills, NoActiveResumeError
    from app.services.email_notifier import send_daily_summary_email
except Exception:
    # exc_info=True로 스택트레이스까지 통째로 로그 파일에 남긴다.
    logger.exception("모듈 임포트 실패 — 스케줄러가 .venv가 아닌 다른 파이썬을 쓰고 있는지 확인하세요.")
    raise

# 이메일에 최소 이 정도 건수는 채우려고 시도하는 목표치.
TARGET_EMAIL_COUNT = 5

# 하루 실행당 새로 분석(LLM 호출)하는 공고 개수 상한. 관련도 필터를 통과한 게 예상보다 많아도
# 이 개수를 넘기면 그날 실행은 여기서 멈춘다 — 비용 폭주를 막는 최종 안전장치.
MAX_NEW_POSTINGS_PER_RUN = 20


# 오늘 새로 분석된 (JobPosting, FitScore) 목록을 받아서, 이메일에 넣을 최종 목록을 고른다.
# 강력추천+추천 -> 점수 높은 순. 그게 목표치보다 적으면 review 등급 중 점수 높은 순으로 채운다.
def build_email_list(new_results: list[tuple[JobPosting, FitScore]]) -> list[tuple[JobPosting, FitScore]]:
    top = [pair for pair in new_results if pair[1].grade in (FitGrade.STRONG_RECOMMEND, FitGrade.RECOMMEND)]
    top.sort(key=lambda pair: pair[1].score, reverse=True)

    if len(top) >= TARGET_EMAIL_COUNT:
        return top

    review = [pair for pair in new_results if pair[1].grade == FitGrade.REVIEW]
    review.sort(key=lambda pair: pair[1].score, reverse=True)

    shortfall = TARGET_EMAIL_COUNT - len(top)
    return top + review[:shortfall]


# 예전에 제외(❌)하면서 사용자가 남긴 키워드 전부 (중복 제거). 이 키워드가 본문에 들어있는
# 새 공고는 LLM 분석 전에 걸러진다.
def get_exclude_keywords(db, user_id: int) -> list[str]:
    rows = (
        db.query(UserFeedback.exclude_keyword)
        .filter(
            UserFeedback.user_id == user_id,
            UserFeedback.action == FeedbackAction.EXCLUDED,
            UserFeedback.exclude_keyword.isnot(None),
        )
        .distinct()
        .all()
    )
    return [row[0] for row in rows]


def main():
    logger.info("=== 데일리 매칭 에이전트 시작 ===")
    db = SessionLocal()
    try:
        user = get_or_create_default_user(db)

        try:
            self_reported_skills, verified_skills, experience_context, skill_frequency = collect_user_skills(db, user.id)
        except NoActiveResumeError:
            logger.info("활성 이력서가 없습니다. 오늘 자동 매칭을 건너뜁니다.")
            return

        # 검색(keywords)과 관련도 판단(relevant_terms)의 기준을 분리한다.
        # keywords는 사이트 검색이 잘 걸리도록 직무명까지 포함한 넓은 문구,
        # relevant_terms는 실제로 내가 가진 개별 기술명만 모은, 본문 대조용 좁은 목록.
        relevant_terms = list(dict.fromkeys(self_reported_skills + verified_skills))
        exclude_keywords = get_exclude_keywords(db, user.id)
        if exclude_keywords:
            logger.info(f"제외 키워드 {len(exclude_keywords)}개 적용: {exclude_keywords}")

        logger.info("검색 키워드 확인 중...")
        keywords, regenerated = get_search_keywords(db, user, skill_frequency, experience_context)
        if regenerated:
            logger.info(f"이력서/포트폴리오/관심표시가 바뀌어 키워드를 새로 생성했습니다 ({len(keywords)}개): {keywords}")
        else:
            logger.info(f"이전에 생성한 키워드를 재사용합니다 ({len(keywords)}개): {keywords}")

        urls: set[str] = set()
        for site_name, search_fn in (("사람인", search_saramin), ("잡코리아", search_jobkorea)):
            try:
                site_urls = search_fn(keywords)
                urls.update(site_urls)
                logger.info(f"{site_name}: {len(site_urls)}개 URL 수집")
            except Exception as e:
                # 사이트 하나가 구조 변경/차단 등으로 실패해도 다른 사이트 결과는 살려서 계속 진행
                logger.info(f"{site_name} 검색 실패, 건너뜀: {e}")

        logger.info(f"총 후보 URL {len(urls)}개")

        new_results: list[tuple[JobPosting, FitScore]] = []
        for i, url in enumerate(urls, start=1):
            if len(new_results) >= MAX_NEW_POSTINGS_PER_RUN:
                logger.info(f"하루 분석 상한({MAX_NEW_POSTINGS_PER_RUN}건)에 도달해 나머지 URL은 건너뜁니다.")
                break

            try:
                posting, skipped = analyze_or_get_existing(
                    db, user, url, relevant_terms=relevant_terms, exclude_keywords=exclude_keywords
                )
            except NotRelevantError as e:
                logger.info(f"[{i}/{len(urls)}] {e}")
                continue
            except ExcludedByKeywordError as e:
                logger.info(f"[{i}/{len(urls)}] {e}")
                continue
            except Exception as e:
                # URL 하나의 문제(페이지 접속 실패 등)로 그날 전체 실행이 죽지 않게 개별 처리.
                # 같은 db 세션을 계속 재사용하므로, 실패 후 세션을 깨끗한 상태로 되돌려야
                # 다음 URL 처리에 영향이 없다.
                db.rollback()
                logger.info(f"[{i}/{len(urls)}] 분석 실패, 건너뜀: {url} ({e})")
                continue

            if skipped:
                logger.info(f"[{i}/{len(urls)}] 이미 있음, 스킵: {url}")
                continue  # 이미 알고 있는 공고 — 오늘 새로 알릴 대상이 아님

            logger.info(f"[{i}/{len(urls)}] 신규 분석 완료: {posting.company} - {posting.title}")

            try:
                fit_score, _ = calculate_and_save_fitscore(db, user, posting)
            except NoActiveResumeError:
                logger.info("적합도 계산 중 활성 이력서가 사라졌습니다. 나머지는 건너뜁니다.")
                break
            except Exception as e:
                # 이 공고 하나의 LLM 응답 문제로 나머지 공고 처리와 이메일 발송까지 전부 무산되지 않게 개별 처리.
                db.rollback()
                logger.info(f"[{i}/{len(urls)}] 적합도 계산 실패, 건너뜀: {posting.url} ({e})")
                continue

            logger.info(f"    -> 적합도 {fit_score.score}점 ({fit_score.grade})")
            new_results.append((posting, fit_score))

        logger.info(f"신규 공고 {len(new_results)}건 분석 완료")

        email_list = build_email_list(new_results)
        if email_list:
            send_daily_summary_email(email_list)
            logger.info(f"이메일 발송 완료 ({len(email_list)}건)")
        else:
            logger.info("발송할 만한 공고가 없어 이메일을 건너뜀")

    finally:
        db.close()
        logger.info("=== 데일리 매칭 에이전트 종료 ===")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("데일리 매칭 에이전트 실행 중 처리되지 않은 예외 발생")
        raise