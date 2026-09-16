"use client";

import { useState } from "react";
import { savePortfolioVersion, activatePortfolioVersion, type PortfolioVersionOut } from "@/lib/api";

type Props = {
  versionId: number;
  initialIsSaved: boolean;
  initialIsActive: boolean;
  initialLabel: string | null | undefined;
};

export default function PortfolioSaveControls({
  versionId,
  initialIsSaved,
  initialIsActive,
  initialLabel,
}: Props) {
  const [isSaved, setIsSaved] = useState(initialIsSaved);
  const [isActive, setIsActive] = useState(initialIsActive);
  const [label, setLabel] = useState(initialLabel ?? "");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSave() {
    setPending(true);
    setError(null);
    try {
      const updated: PortfolioVersionOut = await savePortfolioVersion(versionId, label.trim() || undefined);
      setIsSaved(updated.is_saved);
      setIsActive(updated.is_active);
    } catch (err) {
      console.error(err);
      setError("저장에 실패했습니다. 백엔드 서버 연결을 확인해주세요.");
    } finally {
      setPending(false);
    }
  }

  async function handleActivate() {
    setPending(true);
    setError(null);
    try {
      const updated = await activatePortfolioVersion(versionId);
      setIsActive(updated.is_active);
    } catch (err) {
      console.error(err);
      setError("활성 전환에 실패했습니다. 백엔드 서버 연결을 확인해주세요.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="rounded border border-zinc-200 p-4 text-sm dark:border-zinc-800">
      {!isSaved && (
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex flex-1 min-w-[200px] flex-col gap-1">
            <span className="text-zinc-500">이름 (선택, 예: &quot;2026년 상반기 포트폴리오&quot;)</span>
            <input
              type="text"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              disabled={pending}
              className="rounded border border-zinc-300 px-2 py-1 dark:border-zinc-700 dark:bg-zinc-900"
            />
          </label>
          <button
            type="button"
            onClick={handleSave}
            disabled={pending}
            className="rounded bg-zinc-900 px-4 py-1.5 text-white hover:bg-zinc-700 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
          >
            저장하기
          </button>
        </div>
      )}

      {isSaved && (
        <div className="flex items-center gap-3">
          <span className="rounded-full bg-zinc-100 px-3 py-1 text-xs dark:bg-zinc-800">
            저장됨{label && ` · ${label}`}
          </span>
          {isActive ? (
            <span className="rounded-full bg-green-100 px-3 py-1 text-xs text-green-700 dark:bg-green-950 dark:text-green-400">
              ✓ 현재 활성 포트폴리오
            </span>
          ) : (
            <button
              type="button"
              onClick={handleActivate}
              disabled={pending}
              className="rounded border border-zinc-300 px-3 py-1 text-xs hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-800"
            >
              활성으로 전환
            </button>
          )}
        </div>
      )}

      {error && <p className="mt-2 text-xs text-red-600 dark:text-red-400">{error}</p>}
    </div>
  );
}