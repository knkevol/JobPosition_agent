// 저장된 포트폴리오 버전 1개의 상세 페이지. "/portfolio/versions/3"처럼 접속.
import Link from "next/link";
import {
  fetchPortfolioVersionDetail,
  fetchGithubAnalysis,
  type GithubRepoAnalysisOut,
} from "@/lib/api";
import { formatDate } from "@/lib/format";
import PortfolioSaveControls from "@/components/PortfolioSaveControls";

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

export default async function PortfolioVersionDetailPage(
  props: PageProps<"/portfolio/versions/[id]">
) {
  const { id } = await props.params;
  const versionId = Number(id);

  let version: Awaited<ReturnType<typeof fetchPortfolioVersionDetail>> | null = null;
  let errorMessage: string | null = null;

  try {
    version = await fetchPortfolioVersionDetail(versionId);
  } catch (err) {
    errorMessage = err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다.";
  }

  // 프로젝트별 Github 분석 결과를 병렬로 미리 조회. 아직 분석 안 됐거나 분석
  // 자체가 없던 프로젝트는 fetchGithubAnalysis가 404를 던지므로 null로 둔다.
  const analyses: Record<number, GithubRepoAnalysisOut | null> = {};
  if (version) {
    await Promise.all(
      version.projects
        .filter((p) => p.github_url)
        .map(async (p) => {
          try {
            analyses[p.id] = await fetchGithubAnalysis(p.id);
          } catch {
            analyses[p.id] = null;
          }
        })
    );
  }

  return (
    <div className="flex-1 w-full max-w-3xl mx-auto px-6 py-10">
      <Link href="/portfolio/saved" className="text-sm text-zinc-500 hover:underline">
        ← 저장된 포트폴리오 목록으로 돌아가기
      </Link>

      {errorMessage && (
        <div className="mt-4 rounded border border-red-300 bg-red-50 px-4 py-3 text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
          포트폴리오 정보를 불러오지 못했습니다: {errorMessage}
        </div>
      )}

      {version && (
        <>
          <h1 className="mt-4 text-2xl font-semibold">
            {version.label || `포트폴리오 #${version.id}`}
          </h1>
          <p className="mt-1 text-xs text-zinc-400">저장일시: {formatDate(version.created_at)}</p>

          <div className="mt-4">
            <PortfolioSaveControls
              versionId={version.id}
              initialIsSaved={version.is_saved}
              initialIsActive={version.is_active}
              initialLabel={version.label}
            />
          </div>

          <div className="mt-6 space-y-4">
            {version.projects.map((project) => {
              const analysis = analyses[project.id];
              return (
                <div
                  key={project.id}
                  className="rounded border border-zinc-200 p-4 text-sm dark:border-zinc-800"
                >
                  <h3 className="font-medium">{project.title}</h3>

                  {project.description && (
                    <p className="mt-1 whitespace-pre-wrap text-zinc-600 dark:text-zinc-400">
                      {project.description}
                    </p>
                  )}

                  <div className="mt-2">
                    <TagList items={project.tech_stack} />
                  </div>

                  {project.github_url && (
                    <a
                      href={project.github_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-2 inline-block text-blue-600 hover:underline dark:text-blue-400"
                    >
                      {project.github_url}
                    </a>
                  )}

                  {project.github_url && analysis && (
                    <div className="mt-3 space-y-2 border-t border-zinc-100 pt-3 dark:border-zinc-800">
                      <p className="text-xs font-medium text-green-700 dark:text-green-400">
                        ✓ Github 분석 완료
                      </p>
                      <div>
                        <h4 className="text-xs text-zinc-500">검증된 기술스택</h4>
                        <div className="mt-1">
                          <TagList items={analysis.verified_tech} />
                        </div>
                      </div>
                    </div>
                  )}

                  {project.github_url && !analysis && (
                    <p className="mt-2 text-xs text-zinc-500">Github 분석 결과 없음</p>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}