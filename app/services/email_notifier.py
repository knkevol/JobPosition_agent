import smtplib
from datetime import date
from email.mime.text import MIMEText

from app.core.config import get_settings
from app.models.job_posting import JobPosting
from app.models.fit_score import FitScore, FitGrade

GRADE_LABELS = { 
    FitGrade.STRONG_RECOMMEND: "강력 추천",
    FitGrade.RECOMMEND: "추천",
    FitGrade.REVIEW: "검토",
    FitGrade.NOT_RECOMMEND: "비추천",
    }

# postings : 이메일에 넣을 튜플 목록
def send_daily_summary_email(postings: list[tuple[JobPosting, FitScore]]) -> None:
    if not postings:
        return

    settings = get_settings()

    lines = []
    for i, (job_posting, fit_score) in enumerate(postings, start=1):
        grade_label = GRADE_LABELS[fit_score.grade]
        company = job_posting.company or "(회사명 미상)"
        lines.append(
            f"{i}. {company} - {job_posting.title} (적합도 {fit_score.score}, {grade_label})\n   {job_posting.url}"
        )

    today_str = date.today().isoformat()
    subject = f"[매일 채용공고 매칭] {today_str} 신규 {len(postings)}건"
    body = "\n\n".join(lines)

    message = MIMEText(body, _charset="utf-8")
    message["Subject"] = subject
    message["From"] = settings.smtp_user
    message["To"] = settings.notify_email_to

    # SMTP(587) + starttls() 방식 사용
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_app_password)
        server.send_message(message)