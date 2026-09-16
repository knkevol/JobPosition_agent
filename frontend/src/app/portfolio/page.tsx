// 포트폴리오 업로드 페이지. "/portfolio" 주소로 접속하면 보이는 화면.
import Link from "next/link";
import PortfolioUploadForm from "@/components/PortfolioUploadForm";

export default function PortfolioPage() {
  return (
    <div className="flex-1 w-full max-w-3xl mx-auto px-6 py-10">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">포트폴리오 분석</h1>
        <Link href="/portfolio/saved" className="text-sm text-zinc-500 hover:underline">
          저장된 포트폴리오 목록 →
        </Link>
      </div>
      <p className="mt-1 text-sm text-zinc-500">
        PDF 포트폴리오를 업로드하면 프로젝트별 제목/설명/기술스택/Github 링크를 자동으로
        추출합니다. 업로드할 때마다 새 버전으로 쌓이며, 기존 저장된 버전은 지워지지 않습니다.
        분석 결과 화면에서 &quot;저장하기&quot;를 눌러야 재사용 가능한 기록으로 남고, 적합도
        계산에는 저장된 버전 중 &quot;활성&quot;으로 지정된 것 하나만 사용됩니다.
      </p>

      <div className="mt-6">
        <PortfolioUploadForm />
      </div>
    </div>
  );
}