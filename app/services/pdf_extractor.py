import pdfplumber

def extract_text_from_pdf(file) -> str:
    text_parts = []

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    full_text = "\n\n".join(text_parts)

    if not full_text.strip():
        raise ValueError(
            "PDF 텍스트 추출 불가. 이미지 기반 PDF일 수 있습니다."
        )
    return full_text