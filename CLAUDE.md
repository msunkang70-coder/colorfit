# ColorFit

AI 퍼스널컬러 기반 패션 의사결정 엔진. 진단 결과를 실제 쇼핑에 연결한다.

## 핵심 문서
- **기획서:** `ColorFit_상세기획서_v1.3.md` (v1.4, 3,300줄+) — 제품 설계 전체
- **디자인 시스템:** `DESIGN.md` — 서체, 컬러, 스페이싱, 모션
- **Task 추적:** `TASK.md` — 주차별 진행 상황

## 기술 스택
- Frontend: Next.js 15 + React 19 + TypeScript + TailwindCSS + Framer Motion
- Backend: Python 3.13 + FastAPI 0.115 + Pydantic v2 + SQLAlchemy 2.0
- DB: PostgreSQL 17 (Supabase)
- API: Naver Shopping API, Gemini API
- 배포: Vercel (프론트) + Railway (백엔드)
- Redis: MVP 미사용. 스코어 프리컴퓨팅 + DB 인덱스로 대체

## 개발 컨벤션
- Python: snake_case, 4 spaces 들여쓰기
- TypeScript: camelCase (변수/함수), PascalCase (컴포넌트), 2 spaces
- 커밋: `feat:`, `fix:`, `style:`, `chore:` prefix
- 테스트: pytest (백엔드), vitest (프론트엔드). 핵심 서비스 100% 커버리지 목표
- 가상환경 하에서 테스트 진행

## 디자인 시스템
DESIGN.md를 반드시 읽고 UI 구현할 것.
- 서체: Nanum Myeongjo (헤드라인) + Pretendard Variable (본문)
- 액센트: Marsala #964F4C
- 배경: Warm Off-White #F8F6F3
- 모든 시맨틱 컬러는 웜 톤 (표준 초록/빨강/파랑 아님)

## 아키텍처 핵심
- 추천 파이프라인: Profile → Filter → StyleFilter → Score(5축) → Rerank → Gemini(선택) → Reason
- Hard Filter(탈락) vs Soft Score(순위) 분리
- 코디 스코어는 프리컴퓨팅 (outfits.scores JSONB)
- P1 우선 원칙: 퍼스널컬러는 가이드, 제한 아님. H7 필터율 30% 상한

## Fallback 전략
W3에서 밀리면 순서대로 2차로 미룬다:
1. A vs B 비교
2. Top Pick + One-shot
3. 가격비교 (외부 링크만 유지)
4. 스코어링 5축 → 3축(PCF+OF+SF)

핵심 사수 라인: 온보딩 → 코디 피드 → 추천 이유 → save/dislike → 외부 링크

## Task 완료 프로세스 (필수, 모든 Task에 적용)

각 Task가 완료되면 반드시 아래 3단계를 순서대로 수행한다. 건너뛰지 않는다.

### Step 1: 코드 작성 + 테스트
- Task의 요구사항대로 코드를 작성하고 테스트를 실행한다.
- 테스트가 통과하면 커밋한다.

### Step 2: /codex 코드 리뷰 (자동)
- Task의 코드 변경분에 대해 `/codex` 리뷰를 실행한다.
- `/codex` 명령어를 호출하여 독립적인 AI 코드 리뷰를 받는다.
- 리뷰 결과에서 발견된 이슈가 있으면 수정하고 다시 커밋한다.
- 리뷰 통과(pass) 시 다음 단계로 진행한다.

### Step 3: TASK.md 업데이트
- 체크박스를 `[x]`로 변경한다.
- 예상과 다른 결과가 발생하면 해당 Task 옆에 `⚠️ 메모`를 남긴다.
- `/codex`에서 발견된 이슈가 있었다면 `🔧 codex 리뷰 반영: (내용)` 메모를 추가한다.

### 기타 규칙
- Task 하나가 끝나면 즉시 업데이트한다. 여러 Task를 묶어서 나중에 업데이트하지 않는다.
- W3 금요일에 Fallback 판단이 필요하면 TASK.md 상단의 "현재 상태"를 갱신한다.
- 새로운 Task가 생기면 해당 주차에 추가한다. 임의로 삭제하지 않는다.
