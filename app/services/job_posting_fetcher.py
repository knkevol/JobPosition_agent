from urllib.parse import urlparse, parse_qs

from playwright.sync_api import sync_playwright

# 주어진 URL을 브라우저로 열어, 화면의 텍스트를 모두 뽑아 반환
# 상세 내용이 iframe(페이지 안의 하위 페이지)에 따로 렌더링 되는 경우까지 대응
def fetch_page_text(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc
    # url의 ?key=value~~ 부분을 파이썬 딕셔너리로 분해
    query_rec_idx = parse_qs(parsed.query).get("rec_idx", [None])[0]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) # 채용사이트가 headless(화면에 안보이는 브라우저)를 막기 때문에 실제 창이 뜨는 방식으로 구현
        context = browser.new_context(
             user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="ko-KR",
        )
        page = context.new_page()
        # domcontentloaded: 끊임없이 통신하는 사이트에서도 타임아웃 없이 넘어가도록.
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)

        text_parts = [page.inner_text("body")]
        for frame in page.frames:
            if frame == page.main_frame:
                continue

            frame_host = urlparse(frame.url).netloc
            if frame_host != host:
                continue # 페이지 내 다른 사이트의 iframe은 제외

            if query_rec_idx and query_rec_idx not in frame.url:
                continue # 같은 사이트의 다른 채용 공고 iframe 제외

            try:
                frame_text = frame.inner_text("body")
                if frame_text.strip():
                    text_parts.append(frame_text)
            except Exception:
                continue

        browser.close()

    full_text = "\n\n".join(text_parts)
    if not full_text.strip():
        raise ValueError("페이지에서 텍스트를 가져오지 못했습니다.")
    return full_text