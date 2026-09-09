// 채용공고 상세 페이지. 주소가 "/job-postings/5"처럼 오면 폴더명 "[id]"가
// 그 "5"를 받아서 params.id로 넘겨준다.
import Link from "next/link";
import { fetchJobPostingDetail } from "@/lib/api";
import { gradeLabel, formatDate } from "@/lib/format";
import JobActions from "@/components/JobActions";

// 배열(string[])을 뱃지 형태의 태그 목록으로 그려주는 작은 헬퍼 컴포넌트.
// required_skills / preferred_skills / matched_skills 등 6곳에서 똑같은 모양이
// 반복되므로, 매번 <div className="flex flex-wrap gap-2">...</div>를 복붙하는
// 대신 여기서 한 번만 정의해서 재사용한다. export 없이 이 파일 안에서만 쓰는
// "로컬 컴포넌트"다.
function SkillList({ skills }: { skills: string[] }) {
  if (skills.length === 0) {
    return <span className="text-zinc-500">-</span>;
  }
  return (
    <div className="flex flex-wrap gap-2">
      {/* skills 배열의 문자열 자체가 고유하다는 보장이 없어서(스킬명이 겹칠 수 있음),
          key로는 "인덱스-값" 조합을 쓴다. 이 목록은 재정렬/추가삭제가 없는
          고정된 표시용 목록이라 index를 key에 섞어 써도 문제되지 않는다. */}
      {skills.map((skill, i) => (
        <span
          key={`${i}-${skill}`}
          className="rounded-full bg-zinc-100 px-3 py-1 text-xs dark:bg-zinc-800"
        >
          {skill}
        </span>
      ))}
    </div>
  );
}

// PageProps<"/job-postings/[id]">: layout.tsx의 LayoutProps<"/">와 같은 방식의
// Next.js 타입 헬퍼. "이 라우트 경로에서는 params가 어떤 타입이다"를 자동으로
// 추론해준다 ([id] 폴더가 있으므로 params는 Promise<{ id: string }> 형태가 됨).
// 이 타입은 .next/types/routes.d.ts에 next dev가 실행 중일 때 자동 생성되므로,
// 이 파일을 저장한 뒤 next dev가 새 라우트를 감지할 시간이 잠깐 필요할 수 있다.
export default async function JobPostingDetailPage(
  props: PageProps<"/job-postings/[id]">
) {
  // params가 Promise인 이유: Next.js가 동적 라우트 값을 비동기적으로 준비하기
  // 때문 (예: 병렬로 여러 데이터를 준비하는 최적화를 위해). await로 실제 값을 꺼낸다.
  const { id } = await props.params;
  // 주소의 id는 항상 문자열("5")이라, 숫자를 요구하는 fetchJobPostingDetail에
  // 넘기기 전에 Number()로 변환한다.
  const jobId = Number(id);

  let job: Awaited<ReturnType<typeof fetchJobPostingDetail>> | null = null;
  let errorMessage: string | null = null;

  try {
    job = await fetchJobPostingDetail(jobId);
  } catch (err) {
    errorMessage = err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다.";
  }

  return (
    <div className="flex-1 w-full max-w-3xl mx-auto px-6 py-10">
      {/* 목록 페이지("/")로 돌아가는 링크. Next.js의 <Link>는 <a>와 비슷하지만
          페이지 전체를 새로고침하지 않고 클라이언트에서 화면만 바꿔주는 컴포넌트다. */}
      <Link href="/" className="text-sm text-zinc-500 hover:underline">
        ← 목록으로
      </Link>

      {errorMessage && (
        <div className="mt-4 rounded border border-red-300 bg-red-50 px-4 py-3 text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
          공고 정보를 불러오지 못했습니다: {errorMessage}
        </div>
      )}

      {/* job이 null이 아닐 때만 아래 상세 내용을 그린다. TS 입장에서 이 블록 안의
          job은 null이 아님이 보장되므로(narrowing) job.title처럼 바로 접근 가능. */}
      {job && (
        <>
          <h1 className="mt-4 text-2xl font-semibold">{job.title}</h1>
          <p className="mt-1 text-zinc-500">{job.company ?? "-"}</p>

          <dl className="mt-6 grid grid-cols-2 gap-y-2 text-sm">
            {/* 지원상태/피드백 표시 + 변경 버튼을 JobActions 클라이언트 컴포넌트에 위임.
                이 페이지는 서버 컴포넌트라 클릭 이벤트를 못 받으니, 그 부분만
                별도 클라이언트 컴포넌트로 분리해서 끼워 넣는다. */}
            <JobActions
              jobId={job.id}
              initialApplicationStatus={job.application_status}
              initialFeedback={job.feedback}
            />

            <dt className="text-zinc-500">경력</dt>
            <dd>{job.experience_level ?? "-"}</dd>

            <dt className="text-zinc-500">출처</dt>
            <dd>{job.source_site ?? "-"}</dd>

            <dt className="text-zinc-500">등록일</dt>
            <dd>{formatDate(job.created_at)}</dd>

            <dt className="text-zinc-500">원본 공고</dt>
            <dd>
              {/* target="_blank" = 새 탭에서 열기. rel="noopener noreferrer"는
                  새로 열린 탭이 window.opener로 원래 탭을 조작하지 못하게 막는
                  보안 관례 (target="_blank"를 쓸 때 항상 같이 붙이는 조합). */}
              <a
                href={job.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline dark:text-blue-400"
              >
                바로가기
              </a>
            </dd>
          </dl>

          <section className="mt-6">
            <h2 className="font-semibold">필수 스킬</h2>
            <div className="mt-2">
              <SkillList skills={job.required_skills} />
            </div>
          </section>

          <section className="mt-4">
            <h2 className="font-semibold">우대 스킬</h2>
            <div className="mt-2">
              <SkillList skills={job.preferred_skills} />
            </div>
          </section>

          <section className="mt-8 rounded border border-zinc-200 p-4 dark:border-zinc-800">
            <h2 className="font-semibold">적합도 계산 결과</h2>

            {/* job.fit_score가 없으면(아직 계산 안 한 공고) 안내 문구만 보여준다. */}
            {!job.fit_score && (
              <p className="mt-2 text-zinc-500">적합도 계산 결과가 없습니다.</p>
            )}

            {job.fit_score && (
              <div className="mt-2 space-y-3 text-sm">
                <p>
                  점수 <strong>{job.fit_score.score}</strong> / 등급{" "}
                  <strong>{gradeLabel(job.fit_score.grade)}</strong>
                </p>

                <div>
                  <h3 className="text-zinc-500">매칭된 스킬 (검증됨)</h3>
                  <SkillList skills={job.fit_score.verified_matched_skills} />
                </div>

                <div>
                  <h3 className="text-zinc-500">매칭된 스킬 (미검증)</h3>
                  <SkillList skills={job.fit_score.unverified_matched_skills} />
                </div>

                <div>
                  <h3 className="text-zinc-500">부족한 스킬</h3>
                  <SkillList skills={job.fit_score.missing_skills} />
                </div>

                {/* reason은 Optional(string | null)이라, 값이 있을 때만 그린다. */}
                {job.fit_score.reason && (
                  <div>
                    <h3 className="text-zinc-500">판단 근거</h3>
                    <p className="mt-1 whitespace-pre-wrap">{job.fit_score.reason}</p>
                  </div>
                )}

                <p className="text-xs text-zinc-400">
                  계산일시: {formatDate(job.fit_score.calculated_at)}
                </p>
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}