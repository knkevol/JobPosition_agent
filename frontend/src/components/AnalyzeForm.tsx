"use client";

import { useState } from "react";
// next/navigation의 useRouter: App Router용 클라이언트 훅.
// (옛날 Pages Router 방식인 "next/router"의 useRouter와 이름은 같지만 다른 물건이니
// import 경로를 꼭 "next/navigation"으로 써야 한다.)
import { useRouter } from "next/navigation";
import { analyzeJobPosting } from "@/lib/api";

export default function AnalyzeForm() {
  // router.push(주소)를 호출하면, 사용자가 링크를 클릭한 것과 똑같은 효과로
  // 코드에서 페이지 이동을 시킬 수 있다.
  const router = useRouter();

  // 입력창의 URL 값을 이 컴포넌트가 직접 들고 있는다("controlled input" 방식).
  // value={url} + onChange로 연결해서, 사용자가 타이핑할 때마다 이 state가 갱신된다.
  const [url, setUrl] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // <form onSubmit={...}>로 폼 제출을 직접 처리한다.
  // e.preventDefault()가 핵심: 이걸 안 하면 브라우저가 원래 하려던 "폼 제출 -> 페이지
  // 새로고침"이 그대로 일어나서, 우리가 짠 JS 코드(fetch, 로딩표시, 이동)가 무의미해진다.
  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!url.trim()) {
      setError("URL을 입력해주세요.");
      return;
    }

    setPending(true);
    setError(null);
    try {
      // 백엔드가 이 URL의 채용공고를 분석해서(Claude API 호출 포함) 저장하고,
      // 새로 생긴 채용공고의 id를 돌려준다. 몇 초 걸릴 수 있음.
      const result = await analyzeJobPosting(url.trim());
      // 분석 끝나면 그 공고의 상세 페이지로 바로 이동.
      router.push(`/job-postings/${result.job_posting_id}`);
    } catch (err) {
      console.error(err);
      setError("공고 분석에 실패했습니다. URL을 확인하거나 잠시 후 다시 시도해주세요.");
      setPending(false);
    }
    // 성공 시엔 setPending(false)를 안 하는데, 곧 다른 페이지로 이동해서 이 컴포넌트
    // 자체가 화면에서 사라지기 때문 — 실패했을 때만 버튼을 다시 누를 수 있게 풀어준다.
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mb-6 flex flex-wrap items-end gap-3 rounded border border-zinc-200 p-4 text-sm dark:border-zinc-800"
    >
      <label className="flex flex-1 min-w-[240px] flex-col gap-1">
        <span className="text-zinc-500">채용공고 URL로 새 공고 추가</span>
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://..."
          disabled={pending}
          className="rounded border border-zinc-300 px-2 py-1 disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-900"
        />
      </label>

      <button
        type="submit"
        disabled={pending}
        className="rounded bg-zinc-900 px-4 py-1.5 text-white hover:bg-zinc-700 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
      >
        {/* pending 동안 문구를 바꿔서, 사용자가 "아 지금 처리되고 있구나"를 알 수 있게 함.
            LLM 호출이 껴있어서 몇 초 걸릴 수 있다는 걸 안내. */}
        {pending ? "분석 중... (몇 초 걸릴 수 있어요)" : "분석하기"}
      </button>

      {error && <span className="text-xs text-red-600 dark:text-red-400">{error}</span>}
    </form>
  );
}