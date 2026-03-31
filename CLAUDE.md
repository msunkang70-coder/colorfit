# ColorFit

개인 취향을 반영해 전문가처럼 추천하고, 빠르게 결정하게 만드는 스타일 서비스.

## 현재 단계: v3 Explore Mode 구현 완료 (2026-03-31)

- Task 추적: **TASK_v3.md** (최우선 기준)
- 기획서: **ColorFit_상세기획서_v2.md**
- TASK.md, TASK_v2.md는 아카이브

## UX 구조: Guided Decision

- **Decision Mode (기본):** Top1 코디 + core/evidence/risk_guard + "이걸로 결정" CTA
- **Explore Mode (선택적):** "비슷한 선택 보기" → 축 기반 Top3 compact 카드 → 탭 시 Decision Mode 복귀
- Top5 최대. Top10 이상 금지

## Top3 선발 방식

- feed API에 `page_size=5` 요청 (백엔드 변경 없음)
- 프론트에서 `selectDiverseTop3()` 실행:
  - Top1: 총점 1위
  - Top2: Top1과 다른 1순위 축 보유 코디 중 최고
  - Top3: Top1,2와 다른 축 보유 코디 중 최고
- 축 라벨: pcf=컬러 매칭형, of=상황 최적형, ch=색감 조화형, pe=가성비형, sf=실루엣형

## 절대 금지

1. CTA → 설문 → 이동 흐름 변경 금지 (handleDecide / completeSurvey)
2. backend 수정 금지 (추천/스코어링/필터 포함)
3. Top10 이상 확장 금지
4. 점수 비교 UI 금지
5. 추천 리스트(무한스크롤) 복귀 금지

## 핵심 문서
- **기획서:** `ColorFit_상세기획서_v2.md`
- **디자인 시스템:** `DESIGN.md` — 서체, 컬러, 스페이싱, 모션, Card Variants
- **Task 추적:** `TASK_v3.md`

## 기술 스택
- Frontend: Next.js 15 + React 19 + TypeScript + TailwindCSS + Framer Motion
- Backend: Python 3.13 + FastAPI 0.115 + Pydantic v2 + SQLAlchemy 2.0
- DB: PostgreSQL 17 (Supabase)
- API: Naver Shopping API, Gemini API
- 배포: Vercel (프론트) + Railway (백엔드)
- 측정: sendBeacon + localStorage queue → POST /api/metrics

## 개발 컨벤션
- Python: snake_case, 4 spaces 들여쓰기
- TypeScript: camelCase (변수/함수), PascalCase (컴포넌트), 2 spaces
- 커밋: `feat:`, `fix:`, `style:`, `chore:` prefix
- 테스트: pytest (백엔드), vitest (프론트엔드)
- 가상환경 하에서 테스트 진행

## 디자인 시스템
DESIGN.md를 반드시 읽고 UI 구현할 것.
- 서체: Nanum Myeongjo (헤드라인) + Pretendard Variable (본문)
- 액센트: Marsala #964F4C
- 배경: Warm Off-White #F8F6F3
- 카드: Full (3:4 이미지) / Compact (가로 썸네일 80x100)
- 축 라벨: Marsala pill badge

## 아키텍처 핵심
- 추천 파이프라인: Profile → Filter → StyleFilter → Score(5축) → Rerank → Reason
- Hard Filter(탈락) vs Soft Score(순위) 분리
- 코디 스코어는 프리컴퓨팅 (outfits.scores JSONB)
- Top3 선발은 프론트에서 실행 (축 기반 다양성)

## 측정 데이터
- TTD, CTR, trust_score, confidence
- expanded, expand_level, selected_rank (v3 추가)
- localStorage queue (colorfit_metrics_queue) + 서버 JSONL

## Task 완료 프로세스 (필수)

### Step 1: 코드 작성 + 테스트
### Step 2: /codex 코드 리뷰
### Step 3: TASK_v3.md 업데이트

- Task 하나가 끝나면 즉시 업데이트
- 여러 Task를 묶어서 나중에 업데이트하지 않는다
