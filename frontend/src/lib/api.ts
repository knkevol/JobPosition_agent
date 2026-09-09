// 백엔드(FastAPI) API와 통신하는 함수를 모아둔 파일

// 백엔드 Enum과 유사(ts에 Enum 없음)
export type ApplicationStatus = "not_applied" | "applied";
export type FitGrade = "strong_recommend" | "recommend" | "review" | "not_recommend";
export type FeedbackAction = "interested" | "excluded";

// --- 백엔드 Pydantic 스키마(app/schemas/*.py)와 필드를 1:1로 맞춘 타입들 ---
// 필드명 뒤의 "?"는 Optional(undefined 허용)이라는 뜻으로, 백엔드의 Optional[...] = None과 대응
export interface JobPostingListItem {
  id: number;
  company?: string | null;
  title: string;
  application_status: ApplicationStatus;
  created_at: string;
  fit_score?: number | null;
  fit_grade?: FitGrade | null;
  missing_skills_count?: number | null;
  feedback?: FeedbackAction | null;
}

export interface FitScoreOut {
  id: number;
  user_id: number;
  job_id: number;
  score: number;
  matched_skills: string[];
  verified_matched_skills: string[];
  unverified_matched_skills: string[];
  missing_skills: string[];
  reason?: string | null;
  grade: FitGrade;
  calculated_at: string;
}

export interface JobPostingDetailOut {
  id: number;
  company?: string | null;
  title: string;
  url: string;
  required_skills: string[];
  preferred_skills: string[];
  experience_level?: string | null;
  source_site?: string | null;
  application_status: ApplicationStatus;
  created_at: string;
  feedback?: FeedbackAction | null;
  fit_score?: FitScoreOut | null;
}

// GET /job-postings 의 쿼리 파라미터 (app/api/routes/job_postings.py의 list_job_postings 함수 시그니처와 대응)
// 전부 optional로 둬서, 화면에서 쓰는 필터만 골라 넘긴다.
export interface JobPostingListParams {
  sort_by?: "score" | "company" | "title" | "missing_count" | "created_at";
  order?: "asc" | "desc";
  grade?: FitGrade;
  company?: string;
  min_score?: number;
  application_status?: ApplicationStatus;
  feedback?: FeedbackAction;
  missing_skill?: string;
  limit?: number;
  offset?: number;
}

// .env.local의 NEXT_PUBLIC_API_BASE_URL을 읽습니다. 값이 없으면 로컬 기본값으로 대체 (??는 null/undefined일 때만 대체하는 연산자).
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

// fetch는 404/500이 와도 예외를 던지지 않고 그냥 응답 객체를 반환하므로,
// res.ok(상태코드 200~299 여부)를 직접 확인해서 실패를 에러로 변환해주는 공통 헬퍼
// <T>는 제네릭(generic) — 호출하는 쪽에서 "이 응답을 어떤 타입으로 볼지"를 지정
async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text(); // FastAPI HTTPException(detail=...) 메시지를 최대한 그대로 노출
    throw new Error(`API 요청 실패 (${res.status}): ${body}`);
  }
  return res.json() as Promise<T>;
}

// 채용공고 목록 조회 — GET /job-postings
export async function fetchJobPostings(
  params: JobPostingListParams = {}
): Promise<JobPostingListItem[]> {
  // URLSearchParams: 객체를 "key=value&key2=value2" 형태의 쿼리스트링으로 만들어주는 브라우저 표준 API
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) {
      query.set(key, String(value));
    }
  }

  const res = await fetch(`${API_BASE_URL}/job-postings?${query.toString()}`, {
    cache: "no-store", // Next.js가 fetch 결과를 캐싱하지 않도록 함 — 매번 최신 목록을 받아옴
  });
  return handleResponse<JobPostingListItem[]>(res);
}

// 채용공고 상세 조회 — GET /job-postings/{id}
export async function fetchJobPostingDetail(id: number): Promise<JobPostingDetailOut> {
  const res = await fetch(`${API_BASE_URL}/job-postings/${id}`, { cache: "no-store" });
  return handleResponse<JobPostingDetailOut>(res);
}

// 관심/제외 피드백 등록 — POST /job-postings/{id}/feedback
export async function submitFeedback(id: number, action: FeedbackAction) {
  const res = await fetch(`${API_BASE_URL}/job-postings/${id}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action }),
  });
  return handleResponse<{ id: number; job_id: number; action: FeedbackAction; created_at: string }>(res);
}

// 지원 상태 변경 — PATCH /job-postings/{id}/application-status
export async function updateApplicationStatus(id: number, application_status: ApplicationStatus) {
  const res = await fetch(`${API_BASE_URL}/job-postings/${id}/application-status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ application_status }),
  });
  return handleResponse<{ job_posting_id: number; application_status: ApplicationStatus }>(res);
}

// 채용공고 URL 분석 요청 — POST /job-postings/analyze
export async function analyzeJobPosting(url: string) {
  const res = await fetch(`${API_BASE_URL}/job-postings/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  return handleResponse<{ job_posting_id: number; extracted: Record<string, unknown> }>(res);
}