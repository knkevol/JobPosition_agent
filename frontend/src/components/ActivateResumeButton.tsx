"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { activateResume } from "@/lib/api";

export default function ActivateResumeButton({ resumeId }: { resumeId: number }) {
  const router = useRouter();
  const [pending, setPending] = useState(false);

  async function handleClick() {
    setPending(true);
    try {
      await activateResume(resumeId);
      // 이 페이지(부모)는 서버 컴포넌트라 useState로 화면을 못 바꾼다.
      // router.refresh()는 페이지를 새로고침하지 않고 서버 컴포넌트만 다시
      // 실행시켜서, 방금 바뀐 활성 상태를 최신 데이터로 다시 그리게 한다.
      router.refresh();
    } catch (err) {
      console.error(err);
      alert("활성 전환에 실패했습니다. 백엔드 서버 연결을 확인해주세요.");
    } finally {
      setPending(false);
    }
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={pending}
      className="rounded border border-zinc-300 px-3 py-1 text-xs hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-800"
    >
      활성으로 전환
    </button>
  );
}