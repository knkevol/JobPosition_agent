import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.job_search_fetcher import search_saramin, search_jobkorea

# 실제 이력서 키워드 생성 결과 대신, 확인 목적이라 키워드 1~2개만 간단히 테스트
keywords = ["React"]

print("=== 사람인 ===")
saramin_urls = search_saramin(keywords)
print(f"{len(saramin_urls)}개 발견")
for url in saramin_urls[:10]:
    print(f" - {url}")

print("\n=== 잡코리아 ===")
jobkorea_urls = search_jobkorea(keywords)
print(f"{len(jobkorea_urls)}개 발견")
for url in jobkorea_urls[:10]:
    print(f" - {url}")