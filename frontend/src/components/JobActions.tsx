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
// 서버 컴포넌트에서 이미 fetch로 받아온 최초 값을 그대로 넘겨받아서 시작한다
// (이 컴포넌트가 다시 fetch로 처음부터 조회하지 않아도 됨).
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
  // useState(초기값)은 [현재값, 값을바꾸는함수] 두 개짜리 배열을 반환한다.
  // 예: status는 "현재 화면에 보여줄 지원상태", setStatus(x)를 호출하면
  // status가 x로 바뀌고 이 컴포넌트가 자동으로 다시 그려진다.
  const [status, setStatus] = useState<ApplicationStatus>(initialApplicationStatus);
  const [feedback, setFeedback] = useState<FeedbackAction | null | undefined>(
    initialFeedback
  );
  // 요청이 진행 중일 때 버튼을 잠깐 눌러도 반응 안 하게(중복 클릭 방지) 막는 상태.
  const [pending, setPending] = useState(false);
  // API 호출이 실패했을 때 보여줄 에러 문구. 성공하면 다시 null로 비운다.
  const [error, setError] = useState<string | null>(null);

  // 지원상태 토글: 지금 상태가 "applied"면 "not_applied"로, 아니면 반대로.
  // async function: 이 함수 자체는 async로 선언해도 된다 — "use client" 컴포넌트에서
  // 못 쓰는 건 "컴포넌트 함수 자체"를 async로 만드는 것이고, 그 안의 이벤트 핸들러
  // 함수는 async로 만들어도 문제없다.
  async function toggleStatus() {
    const next: ApplicationStatus = status === "applied" ? "not_applied" : "applied";
    setPending(true);
    setError(null);
    try {
      await updateApplicationStatus(jobId, next);
      setStatus(next); // 서버 응답이 성공한 뒤에야 화면 값을 바꿔서, 실패했는데 바뀐 것처럼 보이는 걸 방지
    }  catch (err) {
      // err.message를 그대로 화면에 보여주면, 백엔드가 꺼져있을 때 브라우저가
      // 만든 "Failed to fetch" 같은 영어 원문이 그대로 노출된다. 사용자에게는
      // 고정된 한국어 문구만 보여주고, 실제 원인은 console.error로 개발자만 보게 남긴다.
      console.error(err);
      setError("지원상태 변경에 실패했습니다. 백엔드 서버 연결을 확인해주세요.");
    } finally {
      // try가 성공하든 catch로 빠지든 항상 실행됨 -> 버튼을 다시 눌러볼 수 있게 풀어줌
      setPending(false);
    }
  }

  // 관심/제외 피드백 등록. action 매개변수로 어느 버튼이 눌렸는지 받는다.
  async function sendFeedback(action: FeedbackAction) {
    setPending(true);
    setError(null);
    try {
      await submitFeedback(jobId, action);
      setFeedback(action);
    } catch (err) {
      console.error(err);
      setError("피드백 등록에 실패했습니다. 백엔드 서버 연결을 확인해주세요.");
    } finally {
      setPending(false);
    }
  }

  // 이 컴포넌트는 부모의 <dl className="grid grid-cols-2 ..."> 안에 그대로
  // 끼워질 예정이라, <div>로 감싸지 않고 <dt>/<dd> 쌍을 바로 반환한다.
  // 여러 요소를 감싸는 태그 없이 묶으려면 <> </> (Fragment)를 쓴다.
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
      <dd className="flex items-center gap-2">
        <span>{feedbackLabel(feedback)}</span>
        <button
          type="button"
          onClick={() => sendFeedback("interested")}
          // 이미 "관심" 상태면 같은 버튼을 또 누를 필요 없게 비활성화
          disabled={pending || feedback === "interested"}
          className="rounded border border-zinc-300 px-2 py-1 text-xs hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-800"
        >
          관심
        </button>
        <button
          type="button"
          onClick={() => sendFeedback("excluded")}
          disabled={pending || feedback === "excluded"}
          className="rounded border border-zinc-300 px-2 py-1 text-xs hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-800"
        >
          제외
        </button>
      </dd>

      {/* error가 있을 때만 렌더링. col-span-2로 grid-cols-2인 부모의 한 줄을
          전부 차지하게 해서 지원상태/피드백 줄과 겹치지 않게 한다. */}
      {error && (
        <dd className="col-span-2 text-xs text-red-600 dark:text-red-400">{error}</dd>
      )}
    </>
  );
}