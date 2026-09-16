// 이력서 분석 상세 페이지. "/resume/3"처럼 접속하면 [id] 폴더가
// "3"을 params.id로 넘겨준다. job-postings/[id]/page.tsx와 같은 방식.
import Link from "next/link";
import { fetchResumeDetail } from "@/lib/api";
import { formatDate } from "@/lib/format";
import ResumeEditForm from "@/components/ResumeEditForm";
import ResumeSaveControls from "@/components/ResumeSaveControls";

// 문자열 배열을 뱃지로 그려주는 로컬 컴포넌트. job-postings/[id]/page.tsx의
// SkillList와 모양이 같지만, 아직 공용 컴포넌트로 분리하지 않고 이 파일 안에서만
// 쓰는 이름(TagList)으로 다시 정의했다 — 기존 파일 구조를 건드리지 않기 위함.
function TagList({ items }: { items: string[] }) {
  if (items.length === 0) {
    return <span className="text-zinc-500">-</span>;
  }
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item, i) => (
        <span
          key={`${i}-${item}`}
          className="rounded-full bg-zinc-100 px-3 py-1 text-xs dark:bg-zinc-800"
        >
          {item}
        </span>
      ))}
    </div>
  );
}

// PageProps<"/resume/[id]">: Next.js가 .next/types/routes.d.ts에 자동 생성하는 타입.
// 이 파일을 저장한 직후엔 next dev가 새 라우트를 아직 못 읽었을 수 있어서,
// 에디터가 잠깐 타입 에러를 보여줄 수 있다(개발 서버가 감지하면 사라짐).
export default async function ResumeDetailPage(
  props: PageProps<"/resume/[id]">
) {
  const { id } = await props.params;
  const resumeId = Number(id);

  let resume: Awaited<ReturnType<typeof fetchResumeDetail>> | null = null;
  let errorMessage: string | null = null;

  try {
    resume = await fetchResumeDetail(resumeId);
  } catch (err) {
    errorMessage = err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다.";
  }

  return (
    <div className="flex-1 w-full max-w-3xl mx-auto px-6 py-10">
      <Link href="/resume" className="text-sm text-zinc-500 hover:underline">
        ← 이력서 업로드로 돌아가기
      </Link>

      {errorMessage && (
        <div className="mt-4 rounded border border-red-300 bg-red-50 px-4 py-3 text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
          이력서 정보를 불러오지 못했습니다: {errorMessage}
        </div>
      )}

      {resume && (
        <>
          <h1 className="mt-4 text-2xl font-semibold">이력서 분석 결과 #{resume.id}</h1>
          <p className="mt-1 text-xs text-zinc-400">분석일시: {formatDate(resume.created_at)}</p>

          <div className="mt-4">
            <ResumeSaveControls
              resumeId={resume.id}
              initialIsSaved={resume.is_saved}
              initialIsActive={resume.is_active}
              initialLabel={resume.label}
            />
          </div>

          <section className="mt-6">
            <h2 className="font-semibold">스킬</h2>
            <div className="mt-2">
              <TagList items={resume.skills} />
            </div>
          </section>

          <section className="mt-4">
            <h2 className="font-semibold">자기 기재 기술</h2>
            <div className="mt-2">
              <TagList items={resume.self_reported_tech} />
            </div>
          </section>

          <section className="mt-6">
            <h2 className="font-semibold">경력</h2>
            {resume.experience.length === 0 && <p className="mt-2 text-zinc-500">-</p>}
            <ul className="mt-2 space-y-3">
              {resume.experience.map((item, i) => (
                <li
                  key={i}
                  className="rounded border border-zinc-200 p-3 text-sm dark:border-zinc-800"
                >
                  <p className="font-medium">
                    {item.company} · {item.role}
                  </p>
                  <p className="text-xs text-zinc-500">{item.period}</p>
                  {item.description && (
                    <p className="mt-1 whitespace-pre-wrap">{item.description}</p>
                  )}
                </li>
              ))}
            </ul>
          </section>

          <section className="mt-6">
            <h2 className="font-semibold">학력</h2>
            {resume.education.length === 0 && <p className="mt-2 text-zinc-500">-</p>}
            <ul className="mt-2 space-y-2">
              {resume.education.map((item, i) => (
                <li key={i} className="text-sm">
                  {item.school}
                  {item.degree && ` · ${item.degree}`}
                  {item.period && ` · ${item.period}`}
                </li>
              ))}
            </ul>
          </section>

          <section className="mt-8">
            <h2 className="font-semibold">스킬 수정</h2>
            <p className="mt-1 text-xs text-zinc-500">
              분석 결과에서 빠졌거나 잘못 인식된 스킬이 있다면 직접 고칠 수 있습니다.
            </p>
            <ResumeEditForm
              resumeId={resume.id}
              initialSkills={resume.skills}
              initialSelfReportedTech={resume.self_reported_tech}
            />
          </section>
        </>
      )}
    </div>
  );
}