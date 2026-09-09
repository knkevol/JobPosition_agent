// 여러 페이지(목록/상세)에서 공통으로 쓰는 "영문 코드값 -> 한글 라벨" /
// "날짜 문자열 -> 보기 좋은 형식" 변환 함수 모음.
// 원래 app/page.tsx 안에 있던 함수들을 여기로 옮겨서, 상세 페이지에서도
// import해서 재사용할 수 있게 만든 것 (같은 로직을 두 파일에 복붙하지 않기 위함).
import type { ApplicationStatus, FeedbackAction, FitGrade } from "@/lib/api";

// TS의 유니온 타입(ApplicationStatus = "not_applied" | "applied")을 매개변수로 받으면,
// switch문에서 각 case를 다 처리했는지 에디터/타입체커가 체크해줄 수 있다.
export function statusLabel(status: ApplicationStatus): string {
  switch (status) {
    case "not_applied":
      return "미지원";
    case "applied":
      return "지원완료";
  }
}

export function gradeLabel(grade: FitGrade | null | undefined): string {
  // grade는 Optional이라 null/undefined가 올 수 있다. 적합도 계산을 안 한 공고는
  // 이 값이 없다.
  switch (grade) {
    case "strong_recommend":
      return "적극 추천";
    case "recommend":
      return "추천";
    case "review":
      return "검토 필요";
    case "not_recommend":
      return "비추천";
    default:
      // null, undefined 둘 다 여기로 떨어진다.
      return "-";
  }
}
export function feedbackLabel(feedback: FeedbackAction | null | undefined): string {
  switch (feedback) {
    case "interested":
      return "관심";
    case "excluded":
      return "제외";
    default:
      return "-";
  }
}

// created_at, calculated_at 등 백엔드가 ISO 8601 문자열로 내려주는 값을
// new Date(문자열)로 JS Date 객체로 만들고, toLocaleDateString으로
// "2026. 9. 1." 같은 한국 로캘(locale) 형식 문자열로 바꾼다.
export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("ko-KR");
}

// 필터 드롭다운(<select>)에 쓸 "값-한글라벨" 쌍 목록.
// statusLabel 등의 switch문과 라벨은 같은데, 드롭다운은 "선택 가능한 값 전체 목록"이
// 필요해서 배열 형태로 따로 정의해둔다.
export const GRADE_OPTIONS: { value: FitGrade; label: string }[] = [
  { value: "strong_recommend", label: "적극 추천" },
  { value: "recommend", label: "추천" },
  { value: "review", label: "검토 필요" },
  { value: "not_recommend", label: "비추천" },
];

export const APPLICATION_STATUS_OPTIONS: { value: ApplicationStatus; label: string }[] = [
  { value: "not_applied", label: "미지원" },
  { value: "applied", label: "지원완료" },
];

export const FEEDBACK_OPTIONS: { value: FeedbackAction; label: string }[] = [
  { value: "interested", label: "관심" },
  { value: "excluded", label: "제외" },
];