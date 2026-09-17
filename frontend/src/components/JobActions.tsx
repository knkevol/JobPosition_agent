"use client";

import { useState } from "react";
import {
  updateApplicationStatus,
  submitFeedback,
  type ApplicationStatus,
  type FeedbackAction,
} from "@/lib/api";
import { statusLabel, feedbackLabel } from "@/lib/format";

// 이 컴포넌트가 부모(상세 페이지)로부터 받는 값들의 타입.
type Props = {
  jobId: number;
  initialApplicationStatus: ApplicationStatus;
  initialFeedback: FeedbackAction | null | undefined;
};

export default function JobActions({
  jobId,
  initialApplicationStatus,
  initialFeedback,
}: Props) {
  const [status, setStatus] = useState<ApplicationStatus>(initialApplicationStatus);
  const [feedback, setFeedback] = useState<FeedbackAction | null | undefined>(
    initialFeedback
  );
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // "제외" 버튼을 누르면 브라우저 기본 window.prompt() 대신 이 인라인 입력창을 펼친다.
  // window.prompt/alert/confirm은 일부 브라우저·임베디드 미리보기 환경에서 차단되어
  // "prompt() is not supported" 에러가 날 수 있어서, 화면에 직접 그리는 <input>으로 대체.
  const [showExcludeInput, setShowExcludeInput] = useState(false);
  const [excludeKeywordInput, setExcludeKeywordInput] = useState("");

  // 지원상태 토글: 지금 상태가 "applied"면 "not_applied"로, 아니면 반대로.
  async function toggleStatus() {
    const next: ApplicationStatus = status === "applied" ? "not_applied" : "applied";
    setPending(true);
    setError(null);
    try {
      await updateApplicationStatus(jobId, next);
      setStatus(next);
    } catch (err) {
      console.error(err);
      setError("지원상태 변경에 실패했습니다. 백엔드 서버 연결을 확인해주세요.");
    } finally {
      setPending(false);
    }
  }

  // 관심/제외 피드백 등록. excludeKeyword는 "제외"일 때만 선택적으로 같이 보낸다.
  async function sendFeedback(action: FeedbackAction, excludeKeyword?: string) {
    setPending(true);
    setError(null);
    try {
      await submitFeedback(jobId, action, excludeKeyword);
      setFeedback(action);
      // 성공하면 입력창은 닫아둔다 (다시 "제외" 눌러야 재입력 가능)
      setShowExcludeInput(false);
      setExcludeKeywordInput("");
    } catch (err) {
      console.error(err);
      setError("피드백 등록에 실패했습니다. 백엔드 서버 연결을 확인해주세요.");
    } finally {
      setPending(false);
    }
  }

  return (
    <>
      <dt className="text-zinc-500">지원상태</dt>
      <dd>
        <button
          type="button"
          onClick={toggleStatus}
          disabled={pending}
          className="rounded border border-zinc-300 px-2 py-1 text-xs hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-800"
        >
          {statusLabel(status)} (클릭해서 변경)
        </button>
      </dd>

      <dt className="text-zinc-500">피드백</dt>
      <dd className="flex flex-col gap-2">
        <div className="flex items-center gap-2">
          <span>{feedbackLabel(feedback)}</span>
          <button
            type="button"
            onClick={() => sendFeedback("interested")}
            disabled={pending || feedback === "interested"}
            className="rounded border border-zinc-300 px-2 py-1 text-xs hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-800"
          >
            관심
          </button>
          <button
            type="button"
            // 다시 누르면 열림/닫힘이 토글되게. (prev) => !prev 형태를 쓰면 이 시점의
            // 최신 상태값을 안전하게 뒤집을 수 있다 (showExcludeInput을 직접 참조하는 것보다 안전).
            onClick={() => setShowExcludeInput((prev) => !prev)}
            disabled={pending || feedback === "excluded"}
            className="rounded border border-zinc-300 px-2 py-1 text-xs hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-800"
          >
            제외
          </button>
        </div>

        {/* "제외" 버튼을 눌렀을 때만 나타나는 인라인 입력창 */}
        {showExcludeInput && (
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={excludeKeywordInput}
              onChange={(e) => setExcludeKeywordInput(e.target.value)}
              placeholder="제외 사유 키워드 (선택사항)"
              className="rounded border border-zinc-300 px-2 py-1 text-xs dark:border-zinc-700 dark:bg-zinc-900"
            />
            <button
              type="button"
              onClick={() => sendFeedback("excluded", excludeKeywordInput.trim() || undefined)}
              disabled={pending}
              className="rounded border border-zinc-300 px-2 py-1 text-xs hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-800"
            >
              제외 확정
            </button>
            <button
              type="button"
              onClick={() => {
                setShowExcludeInput(false);
                setExcludeKeywordInput("");
              }}
              disabled={pending}
              className="text-xs text-zinc-500 hover:underline"
            >
              취소
            </button>
          </div>
        )}
      </dd>

      {error && (
        <dd className="col-span-2 text-xs text-red-600 dark:text-red-400">{error}</dd>
      )}
    </>
  );
}