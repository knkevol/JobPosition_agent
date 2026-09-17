import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.services.user_service import get_or_create_default_user
from app.services.fit_score_service import collect_user_skills, NoActiveResumeError
from app.services.search_keyword_service import get_search_keywords

db = SessionLocal()
try:
    user = get_or_create_default_user(db)
    _self, _verified, experience_context, skill_frequency = collect_user_skills(db, user.id)

    keywords1, regenerated1 = get_search_keywords(db, user, skill_frequency, experience_context)
    print(f"1차 호출 — regenerated={regenerated1}, 키워드 {len(keywords1)}개")

    keywords2, regenerated2 = get_search_keywords(db, user, skill_frequency, experience_context)
    print(f"2차 호출 — regenerated={regenerated2}, 키워드 {len(keywords2)}개")

    print("동일 키워드 재사용 확인됨" if not regenerated2 else "경고: 2차 호출에서도 재생성됨")
except NoActiveResumeError as e:
    print(e)
finally:
    db.close()