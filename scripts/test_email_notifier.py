import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.email_notifier import send_daily_summary_email
from app.models.job_posting import JobPosting
from app.models.fit_score import FitScore, FitGrade

# DB에 저장하지 않고, 이메일 포맷만 확인할 가짜 값을 담은 파이썬 객체.
# db.add()를 안 했으니 실제로 저장되지 않고 메모리에만 존재한다.
job = JobPosting(id=0, company="테스트회사", title="테스트 백엔드 개발자", url="https://example.com/test-posting")
fit = FitScore(id=0, score=88, grade=FitGrade.STRONG_RECOMMEND)

send_daily_summary_email([(job, fit)])
print("전송 완료 — 메일함을 확인하세요.")