import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import resumes, job_postings, fit_scores

app = FastAPI(
    title="AI 채용공고 매칭 에이전트",
    description="이력서·포트폴리오·GitHub 분석 기반 채용공고 적합도 평가 API",
    version="0.1.0",
)

# CORS : 브라우저는 기본적으로 다른 주소로의 접근을 막는데, 프론트엔드에서 이 API를 호출할 수 있게 미리 허용.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resumes.router)
app.include_router(job_postings.router)
app.include_router(fit_scores.router)

# 서버가 살아있는지 확인하는 가장 기본적인 엔드포인트
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "job-matching-agent"}