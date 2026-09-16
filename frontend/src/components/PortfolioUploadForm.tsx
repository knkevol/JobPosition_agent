"use client";

import { useState } from "react";
import {
  analyzePortfolio,
  analyzeAllGithubRepos,
  fetchGithubAnalysis,
  type PortfolioProjectExtraction,
  type GithubRepoAnalysisOut,
} from "@/lib/api";
import { formatDate } from "@/lib/format";
import PortfolioSaveControls from "@/components/PortfolioSaveControls";

// 기술스택/언어 배열을 뱃지 형태로 그려주는 로컬 컴포넌트.
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

// 백엔드가 준 프로젝트 정보(PortfolioProjectExtraction)에, 화면에서만 쓰는
// id + Github 분석 진행상황 필드를 얹은 타입. "&"는 교차 타입(intersection) —
// 기존 필드를 전부 유지한 채로 새 필드들을 추가한다.
// githubStatus 4가지 의미:
//   - "skipped": 이 프로젝트엔 github_url이 없어서 애초에 분석 대상이 아님
//   - "pending": github_url은 있는데 아직 분석 결과가 안 옴 (진행 중)
//   - "ok": 분석 성공
//   - "failed": 분석 시도했지만 실패 (비공개 저장소 등)
type ProjectDisplay = PortfolioProjectExtraction & {
  id: number;
  githubStatus: "skipped" | "pending" | "ok" | "failed";
  githubDetail?: string;
  githubAnalysis?: GithubRepoAnalysisOut;
};

export default function PortfolioUploadForm() {
  const [file, setFile] = useState<File | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // 지금 두 단계 중 어디를 진행 중인지 버튼 문구에 보여주기 위한 상태.
  // null이면 "분석하기"(대기 상태) 문구를 그대로 쓴다.
  const [phase, setPhase] = useState<string | null>(null);
  // 1단계(텍스트 추출)는 성공했는데 2단계(Github 분석)만 실패했을 때 쓰는
  // 별도 에러 상태. error와 분리해둔 이유는 아래 handleSubmit 주석 참고.
  const [githubError, setGithubError] = useState<string | null>(null);

  const [result, setResult] = useState<ProjectDisplay[] | null>(null);
  // 방금 업로드로 새로 만들어진 버전의 id. 저장/활성 컨트롤이 이 값을 필요로 한다.
  const [versionId, setVersionId] = useState<number | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!file) {
      setError("PDF 파일을 선택해주세요.");
      return;
    }

    setPending(true);
    setError(null);
    setGithubError(null);
    setResult(null);
    setVersionId(null);
    setPhase("PDF에서 프로젝트 정보 추출 중...");

    // 1단계: PDF 업로드 + 텍스트 추출. 여기서 실패하면 2단계로 넘어갈 것도
    // 없으므로, catch에서 바로 return으로 함수를 끝낸다.
    let projects: ProjectDisplay[];
    try {
      const uploadRes = await analyzePortfolio(file);
      // uploadRes.extracted.projects[i] 와 uploadRes.portfolio_project_ids[i] 는
      // 같은 순서로 대응된다는 게 보장되어 있어서(백엔드 주석 참고), map의
      // 두 번째 인자인 index(i)로 짝지어 id를 붙인다.
      projects = uploadRes.extracted.projects.map((p, i) => ({
        ...p,
        id: uploadRes.portfolio_project_ids[i],
        githubStatus: p.github_url ? ("pending" as const) : ("skipped" as const),
      }));
      setResult(projects); // Github 분석 전에도 이 시점의 결과를 먼저 화면에 보여준다
      setVersionId(uploadRes.portfolio_version_id);
    } catch (err) {
      console.error(err);
      setError("포트폴리오 분석에 실패했습니다. PDF 파일인지 확인하거나 잠시 후 다시 시도해주세요.");
      setPending(false);
      setPhase(null);
      return;
    }

    // 2단계: Github 링크가 있는 프로젝트가 하나라도 있으면 자동으로 이어서 분석.
    // 이 블록을 별도 try/catch로 감싼 이유: 여기서 실패해도 위에서 이미 저장 ·
    // 표시된 프로젝트 정보(setResult(projects))는 그대로 남아있어야 하기 때문 —
    // "텍스트 추출 실패"와 "Github 분석 실패"를 같은 에러로 뭉뚱그리지 않는다.
    if (projects.some((p) => p.github_url)) {
      setPhase("Github 저장소 분석 중... (프로젝트 수에 따라 다소 걸릴 수 있어요)");
      try {
        const { results: summary } = await analyzeAllGithubRepos();
        // Map: [key, value] 쌍의 배열로 만드는 자료구조. portfolio_project_id로
        // 결과를 빠르게 찾아보기 위해, summary 배열을 "id -> 결과" 맵으로 바꾼다.
        const summaryMap = new Map(summary.map((s) => [s.portfolio_project_id, s]));

        // Promise.all(배열.map(async ...)): 여러 상세조회 요청을 동시에 보내고
        // 전부 끝날 때까지 기다린다. 순서대로 하나씩 await하면 프로젝트 개수만큼
        // 왕복시간이 더해지지만, 이렇게 하면 가장 느린 요청 하나만큼만 기다리면 된다.
        const detailed: ProjectDisplay[] = await Promise.all(
          projects.map(async (p) => {
            const s = summaryMap.get(p.id);
            if (!s) return p; // github_url이 없어 애초에 분석 대상이 아니었던 프로젝트

            if (s.status === "failed") {
              return { ...p, githubStatus: "failed" as const, githubDetail: s.detail };
            }

            try {
              // analyze 응답엔 verified_tech만 있고 languages/readme_summary가
              // 없어서, 상세 화면을 위해 GET으로 한 번 더 받아온다.
              const analysis = await fetchGithubAnalysis(p.id);
              return { ...p, githubStatus: "ok" as const, githubAnalysis: analysis };
            } catch (err) {
              // 분석 자체는 성공했는데 상세조회만 실패한 드문 경우 —
              // 최소한 "성공했다"는 상태만 남기고 상세정보는 비워둔다.
              console.error(err);
              return { ...p, githubStatus: "ok" as const };
            }
          })
        );

        setResult(detailed);
      } catch (err) {
        console.error(err);
        setGithubError(
          "Github 저장소 분석에 실패했습니다. 프로젝트 정보 자체는 정상적으로 저장되었습니다."
        );
      }
    }

    setPending(false);
    setPhase(null);
  }

  return (
    <div>
      <form
        onSubmit={handleSubmit}
        className="flex flex-wrap items-end gap-3 rounded border border-zinc-200 p-4 text-sm dark:border-zinc-800"
      >
        <label className="flex flex-1 min-w-[240px] flex-col gap-1">
          <span className="text-zinc-500">포트폴리오 PDF 업로드</span>
          <input
            type="file"
            accept="application/pdf"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            disabled={pending}
            className="text-zinc-700 disabled:opacity-50 dark:text-zinc-300"
          />
        </label>

        <button
          type="submit"
          disabled={pending}
          className="rounded bg-zinc-900 px-4 py-1.5 text-white hover:bg-zinc-700 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
        >
          {/* phase가 있으면(진행 중이면) 그 단계 설명을, 없으면 기본 문구를 보여준다 */}
          {phase ?? "분석하기"}
        </button>

        {error && <span className="text-xs text-red-600 dark:text-red-400">{error}</span>}
      </form>

      {githubError && (
        <p className="mt-2 text-xs text-amber-700 dark:text-amber-400">{githubError}</p>
      )}

      {versionId !== null && (
        <div className="mt-4">
          <PortfolioSaveControls
            versionId={versionId}
            initialIsSaved={false}
            initialIsActive={false}
            initialLabel={null}
          />
        </div>
      )}

      {result && (
        <div className="mt-6 space-y-4">
          <h2 className="font-semibold">분석된 프로젝트 ({result.length}개)</h2>

          {result.length === 0 && (
            <p className="text-zinc-500">추출된 프로젝트가 없습니다.</p>
          )}

          {result.map((project) => (
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

              {/* githubStatus에 따라 Github 분석 진행상황을 프로젝트 카드 안에 이어서 표시 */}
              {project.githubStatus === "pending" && (
                <p className="mt-2 text-xs text-zinc-500">Github 분석 대기/진행 중...</p>
              )}

              {project.githubStatus === "failed" && (
                <p className="mt-2 text-xs text-red-600 dark:text-red-400">
                  Github 분석 실패: {project.githubDetail ?? "알 수 없는 오류"}
                </p>
              )}

              {project.githubStatus === "ok" && (
                <div className="mt-3 space-y-2 border-t border-zinc-100 pt-3 dark:border-zinc-800">
                  <p className="text-xs font-medium text-green-700 dark:text-green-400">
                    ✓ Github 분석 완료
                  </p>

                  {/* 상세조회(fetchGithubAnalysis)까지 성공했을 때만 언어/요약 표시 */}
                  {project.githubAnalysis && (
                    <>
                      <div>
                        <h4 className="text-xs text-zinc-500">사용 언어</h4>
                        <div className="mt-1">
                          <TagList items={project.githubAnalysis.languages} />
                        </div>
                      </div>

                      <div>
                        <h4 className="text-xs text-zinc-500">검증된 기술스택</h4>
                        <div className="mt-1">
                          <TagList items={project.githubAnalysis.verified_tech} />
                        </div>
                      </div>

                      {project.githubAnalysis.readme_summary && (
                        <div>
                          <h4 className="text-xs text-zinc-500">README 요약</h4>
                          <p className="mt-1 whitespace-pre-wrap text-zinc-600 dark:text-zinc-400">
                            {project.githubAnalysis.readme_summary}
                          </p>
                        </div>
                      )}

                      <p className="text-xs text-zinc-400">
                        분석일시: {formatDate(project.githubAnalysis.analyzed_at)}
                      </p>
                    </>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}