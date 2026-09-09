// 채용공고 목록 페이지.
// "use client" 선언이 없으므로 이 파일은 서버 컴포넌트다 — Next.js 서버(Node.js)에서
// 실행되어 완성된 HTML을 브라우저로 보내준다. 그래서 브라우저에는 로딩 스피너 없이
// 처음부터 데이터가 채워진 화면이 도착한다.
import Link from "next/link";
import AnalyzeForm from "@/components/AnalyzeForm";
import {
  fetchJobPostings,
  type ApplicationStatus,
  type FeedbackAction,
  type FitGrade,
  type JobPostingListItem,
  type JobPostingListParams,
} from "@/lib/api";
// "@/lib/api"의 "@"는 tsconfig.json에 등록된 경로 별칭(alias)으로 "src/"를 가리킨다.
// 상대경로로 쓰면 "../../lib/api"처럼 폴더 구조에 따라 계속 바뀌어야 하는데,
// "@/..."로 쓰면 파일을 어디로 옮겨도 항상 같은 경로로 써도 된다.
import {
  statusLabel,
  gradeLabel,
  feedbackLabel,
  formatDate,
  GRADE_OPTIONS,
  APPLICATION_STATUS_OPTIONS,
  FEEDBACK_OPTIONS,
} from "@/lib/format";
// 라벨/날짜 변환 함수는 상세 페이지에서도 똑같이 써야 해서 lib/format.ts로 옮겼다
// (여기 있던 statusLabel/gradeLabel/feedbackLabel/formatDate 함수 정의는 삭제).

// 정렬 기준(sort_by), 정렬 방향(order) 드롭다운 값 목록.
// api.ts의 JobPostingListParams 안에 문자열 리터럴 유니온으로만 박혀 있어서
// (별도로 export된 타입이 없음), NonNullable<...["sort_by"]>로 그 타입을 그대로 꺼내와 쓴다
// — "sort_by가 어떤 값들을 가질 수 있는지"가 api.ts에서 바뀌면 여기도 같이 타입 에러로 알려줌.
const SORT_OPTIONS: { value: NonNullable<JobPostingListParams["sort_by"]>; label: string }[] = [
  { value: "created_at", label: "등록일" },
  { value: "score", label: "적합도" },
  { value: "company", label: "회사명" },
  { value: "title", label: "공고명" },
  { value: "missing_count", label: "부족역량 수" },
];

const ORDER_OPTIONS: { value: NonNullable<JobPostingListParams["order"]>; label: string }[] = [
  { value: "desc", label: "내림차순" },
  { value: "asc", label: "오름차순" },
];

// searchParams의 값 하나를 꺼내는 헬퍼.
// Next.js의 searchParams는 같은 키가 여러 번 오면 string[]이 될 수 있어서 그런 경우
// 첫 번째 값만 쓰고, "필터 없음(전체)"으로 선택했을 때 폼이 보내는 빈 문자열("")도
// undefined로 취급한다 (그래야 api.ts가 그 필터를 쿼리스트링에서 빼줌).
function firstValue(value: string | string[] | undefined): string | undefined {
  const v = Array.isArray(value) ? value[0] : value;
  return v || undefined;
}

// export default async function: 이 컴포넌트가 이 파일의 기본 export이고,
// 서버 컴포넌트라서 함수 자체를 async로 선언할 수 있다 (클라이언트 컴포넌트는 불가).
//
// PageProps<"/">: layout.tsx의 LayoutProps<"/">와 같은 방식의 Next.js 타입 헬퍼.
// searchParams는 주소 뒤에 붙는 "?grade=recommend&sort_by=score" 같은 쿼리스트링을
// { grade: "recommend", sort_by: "score" } 같은 객체로 만들어서 넘겨준다 (params와 마찬가지로 Promise).
export default async function Home(props: PageProps<"/">) {
  const searchParams = await props.searchParams;

  // 쿼리스트링에서 필터값들을 꺼낸다. 전부 문자열로 오기 때문에, 숫자가 필요한
  // min_score만 Number()로 변환한다. sort_by/order는 값이 없으면 기본값을 쓴다.
  const grade = firstValue(searchParams.grade) as FitGrade | undefined;
  const company = firstValue(searchParams.company);
  const minScoreRaw = firstValue(searchParams.min_score);
  const minScore = minScoreRaw !== undefined ? Number(minScoreRaw) : undefined;
  const applicationStatus = firstValue(searchParams.application_status) as
    | ApplicationStatus
    | undefined;
  const feedback = firstValue(searchParams.feedback) as FeedbackAction | undefined;
  const sortBy = (firstValue(searchParams.sort_by) ?? "created_at") as NonNullable<
    JobPostingListParams["sort_by"]
  >;
  const order = (firstValue(searchParams.order) ?? "desc") as NonNullable<
    JobPostingListParams["order"]
  >;

  let jobPostings: JobPostingListItem[] = [];
  let errorMessage: string | null = null;

  try {
    // 쿼리스트링에서 뽑은 값들을 그대로 fetchJobPostings에 넘긴다.
    // JobPostingListParams의 모든 필드가 optional이라, undefined인 필터는
    // api.ts 안의 URLSearchParams 만드는 로직에서 자동으로 빠진다.
    jobPostings = await fetchJobPostings({
      grade,
      company,
      min_score: minScore,
      application_status: applicationStatus,
      feedback,
      sort_by: sortBy,
      order,
    });
  } catch (err) {
    // 백엔드 서버가 꺼져있거나, 응답이 실패(4xx/5xx)면 api.ts의 handleResponse가
    // Error를 throw하고, 여기서 catch로 잡힌다.
    errorMessage = err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다.";
  }

  return (
    <div className="flex-1 w-full max-w-5xl mx-auto px-6 py-10">
      <h1 className="text-2xl font-semibold mb-6">채용공고 목록</h1>
       <AnalyzeForm />

      {/* method="GET"인 폼은 제출하면 입력값들을 쿼리스트링으로 만들어서
          "/?grade=recommend&sort_by=score..." 같은 주소로 이동한다. 그러면 이 서버
          컴포넌트가 그 주소로 다시 실행되면서 searchParams에 새 값이 들어오고,
          그 값으로 fetchJobPostings를 다시 호출 -> 필터링된 결과가 나온다.
          클라이언트 컴포넌트(useState 등) 없이 순수 HTML 폼만으로 동작하는 방식. */}
      <form
        method="GET"
        className="mb-6 flex flex-wrap items-end gap-3 rounded border border-zinc-200 p-4 text-sm dark:border-zinc-800"
      >
        <label className="flex flex-col gap-1">
          <span className="text-zinc-500">등급</span>
          {/* defaultValue: 폼이 처음 그려질 때 뭘 선택된 상태로 보여줄지 지정.
              현재 주소의 grade 값을 그대로 넣어서, 필터 적용 후에도 선택값이 유지되게 한다. */}
          <select
            name="grade"
            defaultValue={grade ?? ""}
            className="rounded border border-zinc-300 px-2 py-1 dark:border-zinc-700 dark:bg-zinc-900"
          >
            <option value="">전체</option>
            {GRADE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-zinc-500">회사명</span>
          <input
            type="text"
            name="company"
            defaultValue={company ?? ""}
            placeholder="회사명 검색"
            className="rounded border border-zinc-300 px-2 py-1 dark:border-zinc-700 dark:bg-zinc-900"
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-zinc-500">최소 점수</span>
          <input
            type="number"
            name="min_score"
            defaultValue={minScoreRaw ?? ""}
            min={0}
            max={100}
            className="w-24 rounded border border-zinc-300 px-2 py-1 dark:border-zinc-700 dark:bg-zinc-900"
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-zinc-500">지원상태</span>
          <select
            name="application_status"
            defaultValue={applicationStatus ?? ""}
            className="rounded border border-zinc-300 px-2 py-1 dark:border-zinc-700 dark:bg-zinc-900"
          >
            <option value="">전체</option>
            {APPLICATION_STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-zinc-500">피드백</span>
          <select
            name="feedback"
            defaultValue={feedback ?? ""}
            className="rounded border border-zinc-300 px-2 py-1 dark:border-zinc-700 dark:bg-zinc-900"
          >
            <option value="">전체</option>
            {FEEDBACK_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-zinc-500">정렬 기준</span>
          <select
            name="sort_by"
            defaultValue={sortBy}
            className="rounded border border-zinc-300 px-2 py-1 dark:border-zinc-700 dark:bg-zinc-900"
          >
            {SORT_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-zinc-500">정렬 방향</span>
          <select
            name="order"
            defaultValue={order}
            className="rounded border border-zinc-300 px-2 py-1 dark:border-zinc-700 dark:bg-zinc-900"
          >
            {ORDER_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>

        <button
          type="submit"
          className="rounded bg-zinc-900 px-4 py-1.5 text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
        >
          필터 적용
        </button>
        {/* 일반 링크로 "/"에 쿼리스트링 없이 이동 -> 모든 필터 초기화 */}
        <Link href="/" className="text-zinc-500 hover:underline">
          초기화
        </Link>
      </form>

      {/* JSX 안에서는 { } 블록으로 JS 표현식을 끼워 넣을 수 있다.
          &&는 "왼쪽이 true일 때만 오른쪽을 렌더링"하는 조건부 렌더링 패턴 —
          errorMessage가 null이면 아무것도 안 그리고, 문자열이 있으면(=truthy) 그 아래 div를 그림. */}
      {errorMessage && (
        <div className="rounded border border-red-300 bg-red-50 px-4 py-3 text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
          목록을 불러오지 못했습니다: {errorMessage}
          <br />
          백엔드 서버(uvicorn)가 켜져 있는지 확인해주세요.
        </div>
      )}

      {/* 에러도 없고 목록도 비어있을 때 */}
      {!errorMessage && jobPostings.length === 0 && (
        <p className="text-zinc-500">조건에 맞는 채용공고가 없습니다.</p>
      )}

      {/* 에러가 없고 데이터가 1개 이상 있을 때만 표를 그린다 */}
      {!errorMessage && jobPostings.length > 0 && (
        <div className="overflow-x-auto rounded border border-zinc-200 dark:border-zinc-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-zinc-100 dark:bg-zinc-900">
              <tr>
                <th className="px-4 py-2">회사</th>
                <th className="px-4 py-2">공고명</th>
                <th className="px-4 py-2">지원상태</th>
                <th className="px-4 py-2">적합도</th>
                <th className="px-4 py-2">등급</th>
                <th className="px-4 py-2">부족역량</th>
                <th className="px-4 py-2">피드백</th>
                <th className="px-4 py-2">등록일</th>
              </tr>
            </thead>
            <tbody>
              {/* .map(): 배열의 각 원소(job)를 JSX <tr> 하나로 변환해서, 그 결과 배열을
                  그대로 화면에 그린다. React는 목록을 그릴 때 각 항목을 구분할 "key"가
                  꼭 필요한데(항목이 추가/삭제/순서변경될 때 어떤 DOM을 재사용할지 판단하는 값),
                  여기서는 DB의 고유 id를 key로 쓴다. */}
              {jobPostings.map((job) => (
                <tr
                  key={job.id}
                  className="border-t border-zinc-200 dark:border-zinc-800"
                >
                  {/* company는 Optional(string | null)이라 없을 수도 있음 -> "-"로 대체.
                      "??"는 null/undefined일 때만 오른쪽 값으로 대체하는 널리시 병합 연산자
                      (falsy 전체를 대체하는 "||"와 달리, 빈 문자열 ""이나 0은 그대로 유지됨). */}
                  <td className="px-4 py-2">{job.company ?? "-"}</td>
                  <td className="px-4 py-2">
                    <Link
                      href={`/job-postings/${job.id}`}
                      className="text-blue-600 hover:underline dark:text-blue-400"
                    >
                      {job.title}
                    </Link>
                  </td>
                  <td className="px-4 py-2">{statusLabel(job.application_status)}</td>
                  <td className="px-4 py-2">{job.fit_score ?? "-"}</td>
                  <td className="px-4 py-2">{gradeLabel(job.fit_grade)}</td>
                  <td className="px-4 py-2">{job.missing_skills_count ?? "-"}</td>
                  <td className="px-4 py-2">{feedbackLabel(job.feedback)}</td>
                  <td className="px-4 py-2">{formatDate(job.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}