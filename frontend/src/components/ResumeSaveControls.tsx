"use client";

import { useState } from "react";
import { saveResume, activateResume, type ResumeProfileOut } from "@/lib/api";

type Props = {
  resumeId: number;
  initialIsSaved: boolean;
  initialIsActive: boolean;
  initialLabel: string | null | undefined;
};

export default function ResumeSaveControls({
  resumeId,
  initialIsSaved,
  initialIsActive,
  initialLabel,
}: Props) {
  const [isSaved, setIsSaved] = useState(initialIsSaved);
  const [isActive, setIsActive] = useState(initialIsActive);
  // <input type="text">는 controlled 방식이라 value를 state로 들고 있어야 한다.
  const [label, setLabel] = useState(initialLabel ?? "");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSave() {
    setPending(true);
    setError(null);
    try {
      // label.trim()이 빈 문자열이면 undefined를 보내서, 백엔드엔 null로 저장되게 한다.
      const updated: ResumeProfileOut = await saveResume(resumeId, label.trim() || undefined);
      setIsSaved(updated.is_saved);
      setIsActive(updated.is_active); // save는 항상 활성까지 같이 시키므로 true로 바뀜
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
      const updated = await activateResume(resumeId);
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
      {/* 아직 저장 안 한 상태: 이름 입력 + 저장 버튼만 보여준다 */}
      {!isSaved && (
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex flex-1 min-w-[200px] flex-col gap-1">
            <span className="text-zinc-500">이름 (선택, 예: &quot;백엔드용 이력서&quot;)</span>
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

      {/* 이미 저장된 상태: 저장됨 뱃지 + 활성 상태 표시/전환 버튼 */}
      {isSaved && (
        <div className="flex items-center gap-3">
          <span className="rounded-full bg-zinc-100 px-3 py-1 text-xs dark:bg-zinc-800">
            저장됨{label && ` · ${label}`}
          </span>
          {isActive ? (
            <span className="rounded-full bg-green-100 px-3 py-1 text-xs text-green-700 dark:bg-green-950 dark:text-green-400">
              ✓ 현재 활성 이력서
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