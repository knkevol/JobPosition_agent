// 저장된 이력서 목록 페이지. "/resume/saved" 주소.
import Link from "next/link";
import { fetchSavedResumes } from "@/lib/api";
import { formatDate } from "@/lib/format";
import ActivateResumeButton from "@/components/ActivateResumeButton";

export default async function SavedResumesPage() {
  let resumes: Awaited<ReturnType<typeof fetchSavedResumes>> = [];
  let errorMessage: string | null = null;

  try {
    resumes = await fetchSavedResumes();
  } catch (err) {
    errorMessage = err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다.";
  }

  return (
    <div className="flex-1 w-full max-w-3xl mx-auto px-6 py-10">
      <Link href="/resume" className="text-sm text-zinc-500 hover:underline">
        ← 이력서 업로드로 돌아가기
      </Link>

      <h1 className="mt-4 text-2xl font-semibold">저장된 이력서</h1>
      <p className="mt-1 text-sm text-zinc-500">
        적합도 계산에는 이 중 &quot;활성&quot; 표시가 붙은 이력서 하나만 사용됩니다.
      </p>

      {errorMessage && (
        <div className="mt-4 rounded border border-red-300 bg-red-50 px-4 py-3 text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
          목록을 불러오지 못했습니다: {errorMessage}
        </div>
      )}

      {resumes.length === 0 && !errorMessage && (
        <p className="mt-6 text-zinc-500">아직 저장된 이력서가 없습니다.</p>
      )}

      <div className="mt-6 space-y-3">
        {resumes.map((resume) => (
          <div
            key={resume.id}
            className="flex items-center justify-between rounded border border-zinc-200 p-4 text-sm dark:border-zinc-800"
          >
            <div>
              <Link href={`/resume/${resume.id}`} className="font-medium hover:underline">
                {resume.label || `이력서 #${resume.id}`}
              </Link>
              <p className="mt-1 text-xs text-zinc-400">저장일시: {formatDate(resume.created_at)}</p>
            </div>

            {resume.is_active ? (
              <span className="rounded-full bg-green-100 px-3 py-1 text-xs text-green-700 dark:bg-green-950 dark:text-green-400">
                ✓ 활성
              </span>
            ) : (
              <ActivateResumeButton resumeId={resume.id} />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}