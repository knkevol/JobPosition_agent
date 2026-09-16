"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { analyzeResume } from "@/lib/api";

export default function ResumeUploadForm() {
  const router = useRouter();

  // <input type="file">은 <input type="text">와 달리 브라우저 보안 정책상
  // value를 코드에서 직접 지정(controlled)할 수 없다. 그래서 텍스트 입력처럼
  // value={...}를 쓰는 대신, 사용자가 고른 File 객체 자체를 state로 들고 있는다.
  const [file, setFile] = useState<File | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!file) {
      setError("PDF 파일을 선택해주세요.");
      return;
    }

    setPending(true);
    setError(null);
    try {
      // 백엔드가 PDF 텍스트를 뽑고 Claude API로 분석까지 마친 뒤,
      // 새로 만든 ResumeProfile row의 id를 돌려준다. 몇 초 걸릴 수 있음.
      const result = await analyzeResume(file);
      router.push(`/resume/${result.resume_profile_id}`);
    } catch (err) {
      console.error(err);
      setError("이력서 분석에 실패했습니다. PDF 파일인지 확인하거나 잠시 후 다시 시도해주세요.");
      setPending(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex flex-wrap items-end gap-3 rounded border border-zinc-200 p-4 text-sm dark:border-zinc-800"
    >
      <label className="flex flex-1 min-w-[240px] flex-col gap-1">
        <span className="text-zinc-500">이력서 PDF 업로드</span>
        <input
          type="file"
          accept="application/pdf"
          // e.target.files는 FileList(배열은 아니지만 배열처럼 인덱스로 접근 가능한 객체).
          // 파일선택 취소 시 files가 빈 목록이라 [0]이 undefined가 되므로,
          // ?? null로 "undefined면 null"로 통일해서 타입을 File | null 하나로 유지한다.
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
        {pending ? "분석 중... (몇 초 걸릴 수 있어요)" : "분석하기"}
      </button>

      {error && <span className="text-xs text-red-600 dark:text-red-400">{error}</span>}
    </form>
  );
}