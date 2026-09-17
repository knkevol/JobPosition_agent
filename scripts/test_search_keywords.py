import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.services.fit_score_service import collect_user_skills, NoActiveResumeError
from app.services.search_keyword_generator import generate_search_keywords
from app.services.job_search_fetcher import search_saramin, search_jobkorea

db = SessionLocal()
try:
    _self, _verified, experience_context, skill_frequency = collect_user_skills(db, user_id=1)
except NoActiveResumeError as e:
    print(e)
else:
    keywords = generate_search_keywords(skill_frequency, experience_context)
    print(f"키워드 {len(keywords)}개: {keywords}\n")

    saramin_urls = search_saramin(keywords)
    print(f"사람인: {len(saramin_urls)}개")

    jobkorea_urls = search_jobkorea(keywords)
    print(f"잡코리아: {len(jobkorea_urls)}개")

    total = set(saramin_urls) | set(jobkorea_urls)
    print(f"\n총 후보 URL(중복 제거): {len(total)}개")
finally:
    db.close()