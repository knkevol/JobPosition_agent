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
export async function submitFeedback(id: number, action: FeedbackAction, excludeKeyword?: string) {
  const res = await fetch(`${API_BASE_URL}/job-postings/${id}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, exclude_keyword: excludeKeyword ?? null }),
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

// --- 적합도 계산 관련 타입/함수 (FitScoreResult, fit_scores_calculate) ---

// POST /fit-scores/calculate 가 돌려주는 result 필드
export interface FitScoreCalculateResult {
  score: number;
  matched_skills: string[];
  verified_matched_skills: string[];
  unverified_matched_skills: string[];
  missing_skills: string[];
  reason?: string | null;
  grade: FitGrade;
}

export interface FitScoreCalculateResponse {
  fit_score_id: number;
  base_score: number;
  result: FitScoreCalculateResult;
}

// 적합도 계산 요청 — POST /fit-scores/calculate
export async function calculateFitScore(
  jobPostingId: number
): Promise<FitScoreCalculateResponse> {
  const res = await fetch(`${API_BASE_URL}/fit-scores/calculate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_posting_id: jobPostingId }),
  });
  return handleResponse<FitScoreCalculateResponse>(res);
}

// --- 이력서 관련 타입/함수 (app/schemas/resume.py와 대응) ---

export interface ResumeExperienceItem {
  company: string;
  period: string;
  role: string;
  description?: string | null;
}

export interface ResumeEducationItem {
  school: string;
  degree?: string | null;
  period?: string | null;
}

export interface ResumeProfileOut {
  id: number;
  user_id: number;
  skills: string[];
  experience: ResumeExperienceItem[];
  education: ResumeEducationItem[];
  self_reported_tech: string[];
  created_at: string;
  is_saved: boolean;
  is_active: boolean;
  label?: string | null;
}

// PATCH 요청 바디 — 백엔드 ResumeProfileUpdate와 대응. 전부 optional이라
// 넘긴 필드만 갱신되고 나머지는 그대로 유지된다.
export interface ResumeProfileUpdatePayload {
  skills?: string[];
  experience?: ResumeExperienceItem[];
  education?: ResumeEducationItem[];
  self_reported_tech?: string[];
}

// 이력서 PDF 업로드 + 분석 — POST /resumes/analyze
// 파일을 보낼 땐 JSON이 아니라 "multipart/form-data" 형식을 써야 해서,
// JSON.stringify 대신 브라우저 표준 객체인 FormData를 쓴다.
// formData.append("file", file)로 파일을 담아 fetch의 body에 그대로 넘기면,
// 브라우저가 알아서 Content-Type 헤더(파일 구분용 boundary 문자열 포함)를 채워준다.
// 그래서 headers에 Content-Type을 직접 지정하면 안 된다(넣으면 boundary가 빠져서 깨짐).
export async function analyzeResume(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE_URL}/resumes/analyze`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<{
    resume_profile_id: number;
    extracted: {
      skills: string[];
      experience: ResumeExperienceItem[];
      education: ResumeEducationItem[];
      self_reported_tech: string[];
    };
  }>(res);
}

// 이력서 분석 결과 상세 조회 — GET /resumes/{id}
export async function fetchResumeDetail(id: number): Promise<ResumeProfileOut> {
  const res = await fetch(`${API_BASE_URL}/resumes/${id}`, { cache: "no-store" });
  return handleResponse<ResumeProfileOut>(res);
}

// 이력서 분석 결과 수정 — PATCH /resumes/{id}
export async function updateResume(
  id: number,
  payload: ResumeProfileUpdatePayload
): Promise<ResumeProfileOut> {
  const res = await fetch(`${API_BASE_URL}/resumes/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse<ResumeProfileOut>(res);
}

// 저장된 이력서 목록 조회 — GET /resumes (is_saved=true인 것만 옴)
export async function fetchSavedResumes(): Promise<ResumeProfileOut[]> {
  const res = await fetch(`${API_BASE_URL}/resumes`, { cache: "no-store" });
  return handleResponse<ResumeProfileOut[]>(res);
}

// 이력서 저장 (+ 동시에 활성으로 지정) — POST /resumes/{id}/save
export async function saveResume(id: number, label?: string): Promise<ResumeProfileOut> {
  const res = await fetch(`${API_BASE_URL}/resumes/${id}/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ label: label ?? null }),
  });
  return handleResponse<ResumeProfileOut>(res);
}

// 저장된 이력서 중 하나를 활성으로 전환 — POST /resumes/{id}/activate
export async function activateResume(id: number): Promise<ResumeProfileOut> {
  const res = await fetch(`${API_BASE_URL}/resumes/${id}/activate`, {
    method: "POST",
  });
  return handleResponse<ResumeProfileOut>(res);
}

// --- 포트폴리오 관련 타입/함수 (app/schemas/portfolio.py와 대응) ---
export interface PortfolioProjectExtraction {
  title: string;
  description?: string | null;
  tech_stack: string[];
  github_url?: string | null;
}

export interface PortfolioExtractionResult {
  projects: PortfolioProjectExtraction[];
}

// DB에 저장된 프로젝트 1개 — PortfolioProjectExtraction과 필드는 같지만
// id/created_at까지 포함된, 조회 응답 전용 타입.
export interface PortfolioProjectOut {
  id: number;
  title: string;
  description?: string | null;
  tech_stack: string[];
  github_url?: string | null;
  created_at: string;
}

// 버전(=업로드 한 번) 단위 타입. 이력서의 ResumeProfileOut과 같은 is_saved/
export interface PortfolioVersionOut {
  id: number;
  user_id: number;
  is_saved: boolean;
  is_active: boolean;
  label?: string | null;
  created_at: string;
  projects: PortfolioProjectOut[];
}

// 포트폴리오 PDF 업로드 + 분석 — POST /portfolios/analyze
export async function analyzePortfolio(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE_URL}/portfolios/analyze`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<{
    portfolio_version_id: number;
    portfolio_project_ids: number[];
    extracted: PortfolioExtractionResult;
  }>(res);
}

// 저장된 포트폴리오 버전 목록 조회 — GET /portfolios/versions (is_saved=true인 것만 옴)
export async function fetchSavedPortfolioVersions(): Promise<PortfolioVersionOut[]> {
  const res = await fetch(`${API_BASE_URL}/portfolios/versions`, { cache: "no-store" });
  return handleResponse<PortfolioVersionOut[]>(res);
}

// 포트폴리오 버전 상세 조회 — GET /portfolios/versions/{id}
export async function fetchPortfolioVersionDetail(id: number): Promise<PortfolioVersionOut> {
  const res = await fetch(`${API_BASE_URL}/portfolios/versions/${id}`, { cache: "no-store" });
  return handleResponse<PortfolioVersionOut>(res);
}

// 포트폴리오 버전 저장 (+ 동시에 활성으로 지정) — POST /portfolios/versions/{id}/save
export async function savePortfolioVersion(id: number, label?: string): Promise<PortfolioVersionOut> {
  const res = await fetch(`${API_BASE_URL}/portfolios/versions/${id}/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ label: label ?? null }),
  });
  return handleResponse<PortfolioVersionOut>(res);
}

// 저장된 포트폴리오 버전 중 하나를 활성으로 전환 — POST /portfolios/versions/{id}/activate
export async function activatePortfolioVersion(id: number): Promise<PortfolioVersionOut> {
  const res = await fetch(`${API_BASE_URL}/portfolios/versions/${id}/activate`, {
    method: "POST",
  });
  return handleResponse<PortfolioVersionOut>(res);
}

// --- Github 저장소 분석 관련 타입/함수 (app/schemas/github_analysis.py와 대응) ---
// POST /github-analyses/analyze 응답의 결과 배열 한 항목.
// status가 "ok"일 때만 verified_tech가, "failed"일 때만 detail이 온다
export interface GithubAnalyzeResultItem {
  portfolio_project_id: number;
  title: string;
  status: "ok" | "failed";
  verified_tech?: string[];
  detail?: string;
}

// GET /github-analyses/{id} 응답 — GithubRepoAnalysisOut 스키마와 1:1 대응
export interface GithubRepoAnalysisOut {
  id: number;
  portfolio_project_id: number;
  repo_url: string;
  languages: string[];
  readme_summary?: string | null;
  verified_tech: string[];
  analyzed_at: string;
}

// Github 링크가 있는 내 포트폴리오 프로젝트 전체를 분석 — POST /github-analyses/analyze
// body가 없는 POST 요청이라, fetch에 method만 지정하면 된다 (headers/body 불필요).
export async function analyzeAllGithubRepos(): Promise<{ results: GithubAnalyzeResultItem[] }> {
  const res = await fetch(`${API_BASE_URL}/github-analyses/analyze`, {
    method: "POST",
  });
  return handleResponse<{ results: GithubAnalyzeResultItem[] }>(res);
}

// 프로젝트 1개의 Github 분석 상세 결과 조회 — GET /github-analyses/{portfolio_project_id}
export async function fetchGithubAnalysis(
  portfolioProjectId: number
): Promise<GithubRepoAnalysisOut> {
  const res = await fetch(`${API_BASE_URL}/github-analyses/${portfolioProjectId}`, {
    cache: "no-store",
  });
  return handleResponse<GithubRepoAnalysisOut>(res);
}