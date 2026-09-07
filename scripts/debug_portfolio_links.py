import sys
from pathlib import Path

import pdfplumber

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.services.pdf_extractor import extract_text_from_pdf  # 실제 앱이 쓰는 함수와 동일한 걸 검증

def main(pdf_path: str):
    path = Path(pdf_path)

    print("=" * 60)
    print("1) pdfplumber가 실제로 인식하는 하이퍼링크 주석(annotation) 목록")
    print("=" * 60)
    with pdfplumber.open(path) as pdf:
        found_any = False
        for page_number, page in enumerate(pdf.pages, start=1):
            for link in page.hyperlinks:
                found_any = True
                # uri: 실제 클릭 시 이동하는 완전한 주소. 이게 우리가 원하는 값.
                print(f"  [page {page_number}] uri={link.get('uri')!r}")
        if not found_any:
            print("  (하이퍼링크 주석이 하나도 없습니다 — PDF에 실제 링크 정보가 없다는 뜻)")

    print()
    print("=" * 60)
    print("2) 우리 앱의 extract_text_from_pdf()가 최종적으로 만들어내는 텍스트")
    print("   (여기에 '[문서에 포함된 실제 하이퍼링크 목록]' 섹션이 있는지 확인)")
    print("=" * 60)
    with open(path, "rb") as f:
        text = extract_text_from_pdf(f)

    if "[문서에 포함된 실제 하이퍼링크 목록]" in text:
        # 그 섹션 이후 내용만 잘라서 보여줌
        idx = text.index("[문서에 포함된 실제 하이퍼링크 목록]")
        print(text[idx:])
    else:
        print("  (해당 섹션이 텍스트에 없습니다)")

    print()
    print("=" * 60)
    print("3) 'GameEngine' 문자열 주변 원문 텍스트 (화면에 실제로 어떻게 적혀 있는지)")
    print("=" * 60)
    for line in text.splitlines():
        if "GameEngine" in line or "github" in line.lower():
            print(f"  {line}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python scripts/debug_portfolio_links.py <포트폴리오 PDF 경로>")
        sys.exit(1)
    main(sys.argv[1])