import json
import sys
from pathlib import Path

# Path(__file__): 이 스크립트 파일 자신의 경로
# resolve()로 절대경로로 변경
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.pdf_extractor import extract_text_from_pdf
from app.services.resume_analyzer import analyze_resume_text

BASE_DIR = Path(__file__).resolve().parent.parent / "test_data"
RESUME_DIR = BASE_DIR / "resumes"
GROUND_TRUTH_DIR = BASE_DIR / "ground_truth"
CACHE_DIR = BASE_DIR / "chache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def normalize(skill: str) -> str:
    # 소문자 + 양끝 공백제거
    return skill.strip().lower()

def get_extracted_skills(pdf_path: Path) -> list:
    cache_path = CACHE_DIR / f"{pdf_path.stem}.json" # .stem : 확장자 뺀 파일명

    if cache_path.exists():
        print(f"[캐시 사용] {cache_path.name}")
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)["skills"]

    print(f" [LLM 호출] {pdf_path.name} 분석 중")
    text = extract_text_from_pdf(pdf_path)
    result = analyze_resume_text(text)

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)


    return result.skills

def main():
    pdf_files = sorted(RESUME_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"{RESUME_DIR} 폴더에 PDF가 없습니다.")
        return

    total_recall = []

    for pdf_path in pdf_files:
        gt_path = GROUND_TRUTH_DIR / f"{pdf_path.stem}.json"
        if not gt_path.exists():
            print(f"주의: {pdf_path.name}: 정답 파일({gt_path.name})이 없어서 건너뜁니다.")
            continue

        with open(gt_path, "r", encoding="utf-8") as f:
            ground_truth_skills = json.load(f)["skills"]

        extracted_skills = get_extracted_skills(pdf_path)
        extracted_norm = {normalize(s) for s in extracted_skills}

        matched = [s for s in ground_truth_skills if normalize(s) in extracted_norm]
        missed = [s for s in ground_truth_skills if normalize(s) not in extracted_norm]

        recall = len(matched) / len(ground_truth_skills) if ground_truth_skills else 0.0
        total_recall.append(recall)

        print(f"\n=== {pdf_path.name} ===")
        print(f"정답 기술 수: {len(ground_truth_skills)}건")
        print(f"일치: {matched}")
        print(f"누락: {missed}")
        print(f"재현율: {recall:.0%}")  # :.0% = 0.6 -> "60%" 퍼센트 문자열로 포맷팅

    if total_recall:
        avg = sum(total_recall) / len(total_recall)
        print(f"\n전체 평균 재현율: {avg:.0%} (목표: 90% 이상)")


if __name__ == "__main__":
    main()