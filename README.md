# 📄 *AI 채용공고 매칭 에이전트*
이력서·포트폴리오·GitHub를 LLM으로 분석해 채용공고 적합도를 계산하고, 매일 새 공고를 수집해 추천 메일로 보내는 개인화 에이전트입니다.
<br />

<br />
<br />

***

### ✅ 주요 기능

-  **AI와 사람의 역할을 나눈 협업 워크플로우 설계**
    - CLAUDE.md에 AI의 역할(설계 설명·코드 제시)과 나의 역할(직접 구현·판단·테스트)을 명시하고, LLM API 호출 규칙과 예상 비용 사전 고지 규칙을 정해 Claude Code와 협업
      
      <br />
- **문제 정의와 단계별 구조화**
    - "이력서에 사용한 기술과 포트폴리오 기술은 다르다."는 문제를 먼저 정의하고, 기획서를 작성해 문서 분석 → 공고 분석 → 적합도 계산 → GitHub 검증 → 자동화의 Phase 단위로 나누어 실행
    - LLM 응답을 Pydantic 스키마로 강제하여, AI 출력이 항상 정해진 구조로 DB에 저장되도록 설계

      <br />
- **매일 자동 실행되는 에이전트 완성과 LLM 비용 통제**
    - 활성 이력서와 관심 피드백을 바탕으로 LLM이 검색 키워드를 생성하고, Playwright로 사람인·잡코리아에서 새 공고를 수집해 분석·추천 결과를 이메일로 자동 발송
    - LLM 호출 전에 기술 관련도·제외 키워드·요구 경력으로 1차 필터링하고, 하루 분석 상한(20건)과 결과 캐싱으로 자동 실행과 테스트 비용을 통제

      <br />
- **LLM + GitHub 코드 분석 기반 역량 검증과 적합도 계산**
    - PyGithub로 저장소의 의존성 파일·README·소스코드를 수집하고, LLM이 실제 코드에서 확인한 기술만 "검증된 기술"로 분리
    - GitHub 검증 기술은 1.0, 이력서에만 적힌 기술은 0.6의 신뢰도 가중치로 기준 점수를 계산하고, LLM이 표현 차이를 의미 기준으로 보정해 일치/부족 역량과 추천 이유를 생성
    - GitHub 검증 반영 전후(Phase 3 / Phase 5)의 점수를 비교하는 검증 스크립트로 개선 효과 확인
<br />

***

### ✅ 구조도

<br />
<img width="3200" height="1920" alt="image" src="https://github.com/user-attachments/assets/bd1c699f-d921-4a6d-bb8c-b06a824c41c0" />
<br />
<br />

***


### ✅ 구현 모습

<img width="1079" height="441" alt="image" src="https://github.com/user-attachments/assets/66f2891c-b909-48ce-8a04-0c0271c7b5f8" />

- 공고사이트를 넣어 분석을 돌렸을 때 메인페이지의 리스트에 추가됨.
  
<br />
<br />
<img width="772" height="310" alt="image" src="https://github.com/user-attachments/assets/3bc5eeda-733a-408b-86a3-1dcf3ee0bce3" />
<br />
<img width="820" height="407" alt="image" src="https://github.com/user-attachments/assets/b6462f2f-26ca-4605-aa0f-126b0e5961ca" />

- 이력서 및 포트폴리오를 추가하고 활성화할 항목을 선택
<br />
<br />
<img width="712" height="710" alt="image" src="https://github.com/user-attachments/assets/f61e2bce-6727-4e80-803f-d2cea82736e1" />

- 분석완료된 공고에 현재 활성화된 이력서와 포트폴리오를 기반으로 적합도 분석
<br />
