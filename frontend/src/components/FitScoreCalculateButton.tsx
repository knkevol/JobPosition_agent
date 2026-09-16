"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { calculateFitScore } from "@/lib/api";

// 부모(상세 페이지)로부터 받는 값. hasScore는 "적합도 계산하기" /
// "적합도 다시 계산하기" 중 어떤 문구를 보여줄지 결정하는 용도로만 쓴다.
type Props = {
  jobId: number;
  hasScore: boolean;
};

export default function FitScoreCalculateButton({ jobId, hasScore }: Props) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleClick() {
    setPending(true);
    setError(null);
    try {
      await calculateFitScore(jobId);
      // 이 컴포넌트는 계산 결과를 직접 들고 있지 않는다 — 부모 페이지(서버 컴포넌트)가
      // job.fit_score를 새로 fetch하도록 router.refresh()로 다시 실행시킨다.
      router.refresh();
    } catch (err) {
      console.error(err);
      // 다른 버튼들과 달리 고정 문구가 아니라 err.message를 그대로 보여준다.
      // 활성 이력서가 없을 때(422) 백엔드가 detail에 원인을 정확히 설명해주기 때문.
      setError(err instanceof Error ? err.message : "적합도 계산에 실패했습니다.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="mt-2 flex flex-wrap items-center gap-3">
      <button
        type="button"
        onClick={handleClick}
        disabled={pending}
        className="rounded bg-zinc-900 px-4 py-1.5 text-sm text-white hover:bg-zinc-700 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
      >
        {pending
          ? "계산 중... (몇 초 걸릴 수 있어요)"
          : hasScore
            ? "적합도 다시 계산하기"
            : "적합도 계산하기"}
      </button>

      {error && (
        <span className="text-xs text-red-600 dark:text-red-400">{error}</span>
      )}
    </div>
  );
}