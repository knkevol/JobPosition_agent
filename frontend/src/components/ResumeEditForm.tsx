"use client";

import { useState } from "react";
import { updateResume } from "@/lib/api";

type Props = {
  resumeId: number;
  initialSkills: string[];
  initialSelfReportedTech: string[];
};

// 문자열 배열을 "React, TypeScript, FastAPI" 같은 한 줄 텍스트로 합친다.
// 편집 입력창에 처음 채워 넣을 값을 만들 때 쓴다.
function toText(list: string[]): string {
  return list.join(", ");
}

// 위 함수의 반대: 쉼표로 구분된 텍스트를 다시 문자열 배열로 되돌린다.
// split(",")로 쪼갠 뒤 각 조각 trim()으로 앞뒤 공백 제거, filter(Boolean)으로
// "React, , Python"처럼 쉼표가 중복돼서 생긴 빈 문자열("")을 걸러낸다..
function toList(text: string): string[] {
  return text
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

export default function ResumeEditForm({
  resumeId,
  initialSkills,
  initialSelfReportedTech,
}: Props) {
  const [skillsText, setSkillsText] = useState(toText(initialSkills));
  const [techText, setTechText] = useState(toText(initialSelfReportedTech));
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setPending(true);
    setError(null);
    setSaved(false);
    try {
      // updateResume은 PATCH 요청 — 여기 넘긴 필드(skills, self_reported_tech)만
      // 백엔드의 exclude_unset=True 로직에 의해 갱신되고, experience/education은 그대로 남는다.
      await updateResume(resumeId, {
        skills: toList(skillsText),
        self_reported_tech: toList(techText),
      });
      setSaved(true);
    } catch (err) {
      console.error(err);
      setError("수정 사항을 저장하지 못했습니다. 백엔드 서버 연결을 확인해주세요.");
    } finally {
      setPending(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mt-4 space-y-3 rounded border border-zinc-200 p-4 text-sm dark:border-zinc-800"
    >
      <label className="flex flex-col gap-1">
        <span className="text-zinc-500">스킬 (쉼표로 구분)</span>
        <input
          type="text"
          value={skillsText}
          onChange={(e) => setSkillsText(e.target.value)}
          disabled={pending}
          className="rounded border border-zinc-300 px-2 py-1 disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-900"
        />
      </label>

      <label className="flex flex-col gap-1">
        <span className="text-zinc-500">자기 기재 기술 (쉼표로 구분)</span>
        <input
          type="text"
          value={techText}
          onChange={(e) => setTechText(e.target.value)}
          disabled={pending}
          className="rounded border border-zinc-300 px-2 py-1 disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-900"
        />
      </label>

      <div className="flex items-center gap-3">
        <button
          type="submit"
          disabled={pending}
          className="rounded bg-zinc-900 px-4 py-1.5 text-white hover:bg-zinc-700 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
        >
          {pending ? "저장 중..." : "저장"}
        </button>
        {saved && (
          <span className="text-xs text-green-600 dark:text-green-400">저장됐습니다.</span>
        )}
        {error && <span className="text-xs text-red-600 dark:text-red-400">{error}</span>}
      </div>
    </form>
  );
}