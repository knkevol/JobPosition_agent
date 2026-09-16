import re
from urllib.parse import quote

from playwright.sync_api import sync_playwright

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# 정규화된 상세 URL을 반환. with sync_playwright() 블록 하나 안에서 브라우저/페이지를 한번만 열고 재사용
def search_saramin(keywords: list[str]) -> list[str]:
    urls: set[str] = set() # 중복 제거를 위한 set 사용

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(user_agent=USER_AGENT, locale="ko-KR")
        page = context.new_page()

        for keyword in keywords:
            search_url = (
                f"https://www.saramin.co.kr/zf_user/search/recruit"
                f"?searchword={quote(keyword)}&recruitPage=1&recruitSort=relation"
            )
            page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)

            # rec_idx(공고 고유 ID)가 포함된 href js로 수집
            hrefs = page.eval_on_selector_all("a[href*='rec_idx=']", "elements => elements.map(el => el.href)")

            for href in hrefs:
                match = re.search(r"rec_idx=(\d+)", href)
                if match:
                    urls.add(f"https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx={match.group(1)}")

        browser.close()

    return list(urls)

# 잡코리아 버전. 구조는 search_saramin과 동일하고, URL 패턴/선택자만 다름.
def search_jobkorea(keywords: list[str]) -> list[str]:
    urls: set[str] = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(user_agent=USER_AGENT, locale="ko-KR")
        page = context.new_page()

        for keyword in keywords:
            search_url = f"https://www.jobkorea.co.kr/Search/?stext={quote(keyword)}"
            page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)

            hrefs = page.eval_on_selector_all(
                "a[href*='/Recruit/GI_Read/']", "elements => elements.map(el => el.href)"
            )
            for href in hrefs:
                match = re.search(r"/Recruit/GI_Read/(\d+)", href)
                if match:
                    # listno/sc/logpath 같은 추적 쿼리 다 버리고 공고 ID만 남김
                    urls.add(f"https://www.jobkorea.co.kr/Recruit/GI_Read/{match.group(1)}")

        browser.close()

    return list(urls)

def search_all_sites(keywords: list[str]) -> list[str]:
    urls = set(search_saramin(keywords))
    urls.update(search_jobkorea(keywords))
    return list(urls)