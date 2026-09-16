// 저장된 포트폴리오 버전 목록 페이지. "/portfolio/saved" 주소.
import Link from "next/link";
import { fetchSavedPortfolioVersions } from "@/lib/api";
import { formatDate } from "@/lib/format";
import ActivatePortfolioVersionButton from "@/components/ActivatePortfolioVersionButton";

export default async function SavedPortfolioVersionsPage() {
  let versions: Awaited<ReturnType<typeof fetchSavedPortfolioVersions>> = [];
  let errorMessage: string | null = null;

  try {
    versions = await fetchSavedPortfolioVersions();
  } catch (err) {
    errorMessage = err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다.";
  }

  return (
    <div className="flex-1 w-full max-w-3xl mx-auto px-6 py-10">
      <Link href="/portfolio" className="text-sm text-zinc-500 hover:underline">
        ← 포트폴리오 업로드로 돌아가기
      </Link>

      <h1 className="mt-4 text-2xl font-semibold">저장된 포트폴리오</h1>
      <p className="mt-1 text-sm text-zinc-500">
        적합도 계산에는 이 중 &quot;활성&quot; 표시가 붙은 버전 하나만 사용됩니다.
      </p>

      {errorMessage && (
        <div className="mt-4 rounded border border-red-300 bg-red-50 px-4 py-3 text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
          목록을 불러오지 못했습니다: {errorMessage}
        </div>
      )}

      {versions.length === 0 && !errorMessage && (
        <p className="mt-6 text-zinc-500">아직 저장된 포트폴리오가 없습니다.</p>
      )}

      <div className="mt-6 space-y-3">
        {versions.map((version) => (
          <div
            key={version.id}
            className="flex items-center justify-between rounded border border-zinc-200 p-4 text-sm dark:border-zinc-800"
          >
            <div>
              <Link href={`/portfolio/versions/${version.id}`} className="font-medium hover:underline">
                {version.label || `포트폴리오 #${version.id}`}
              </Link>
              <p className="mt-1 text-xs text-zinc-400">
                프로젝트 {version.projects.length}개 · 저장일시: {formatDate(version.created_at)}
              </p>
            </div>

            {version.is_active ? (
              <span className="rounded-full bg-green-100 px-3 py-1 text-xs text-green-700 dark:bg-green-950 dark:text-green-400">
                ✓ 활성
              </span>
            ) : (
              <ActivatePortfolioVersionButton versionId={version.id} />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}