import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.models import ResumeProfile
from app.services.search_keyword_generator import generate_search_keywords

db = SessionLocal()
resume = db.query(ResumeProfile).filter(ResumeProfile.is_active.is_(True)).first()
if resume is None:
    print("활성 이력서가 없습니다. /resume/saved에서 하나를 활성으로 지정하세요.")
else:
    keywords = generate_search_keywords(resume)
    print(f"생성된 키워드 {len(keywords)}개:")
    for kw in keywords:
        print(f" - {kw}")
db.close()