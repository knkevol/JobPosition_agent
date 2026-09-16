// 이력서 업로드 페이지. "/resume" 주소로 접속하면 보이는 화면.
// 서버 컴포넌트라 클릭/state를 못 다루므로, 실제 업로드 로직은
// 클라이언트 컴포넌트인 ResumeUploadForm에 전부 위임한다.
import Link from "next/link";
import ResumeUploadForm from "@/components/ResumeUploadForm";

export default function ResumePage() {
  return (
    <div className="flex-1 w-full max-w-3xl mx-auto px-6 py-10">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">이력서 분석</h1>
        <Link href="/resume/saved" className="text-sm text-zinc-500 hover:underline">
          저장된 이력서 목록 →
        </Link>
      </div>
      <p className="mt-1 text-sm text-zinc-500">
        PDF 이력서를 업로드하면 스킬/경력/학력을 자동으로 추출합니다. 분석 결과 화면에서
        &quot;저장하기&quot;를 눌러야 재사용 가능한 기록으로 남고, 적합도 계산에는 저장된
        이력서 중 &quot;활성&quot;으로 지정된 것 하나만 사용됩니다.
      </p>

      <div className="mt-6">
        <ResumeUploadForm />
      </div>
    </div>
  );
}