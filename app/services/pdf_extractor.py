import pdfplumber

def extract_text_from_pdf(file) -> str:
    text_parts = []
    hyperlink_uris = []

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

            for link in page.hyperlinks:
                uri = link.get("uri")
                if uri:
                    hyperlink_uris.append(uri)

    full_text = "\n\n".join(text_parts)

    if not full_text.strip():
        raise ValueError(
            "PDF 텍스트 추출 불가. 이미지 기반 PDF일 수 있습니다."
        )

    if hyperlink_uris:
        unique_links = list(dict.fromkeys(hyperlink_uris))
        full_text += "\n\n[문서에 포함된 실제 하이퍼링크 목록]\n" + "\n".join(unique_links)
    return full_text