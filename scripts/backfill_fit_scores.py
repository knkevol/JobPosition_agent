import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.models.job_posting import JobPosting
from app.models.fit_score import FitScore
from app.services.user_service import get_or_create_default_user
from app.services.fit_score_service import calculate_and_save_fitscore, NoActiveResumeError

db = SessionLocal()
try:
    user = get_or_create_default_user(db)

    # FitScore가 아직 없는(=분석은 됐지만 계산 전에 죽은) 공고만 골라낸다.
    scored_job_ids = {row.job_id for row in db.query(FitScore.job_id).filter(FitScore.user_id == user.id).all()}
    postings = db.query(JobPosting).filter(JobPosting.user_id == user.id).all()
    pending = [p for p in postings if p.id not in scored_job_ids]

    print(f"적합도 미계산 공고 {len(pending)}건")

    done = 0
    for posting in pending:
        try:
            calculate_and_save_fitscore(db, user, posting)
            done += 1
        except NoActiveResumeError as e:
            print(e)
            break
        except Exception as e:
            db.rollback()
            print(f"실패, 건너뜀: {posting.url} ({e})")

    print(f"{done}건 계산 완료")
finally:
    db.close()