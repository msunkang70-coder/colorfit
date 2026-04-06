# ColorFit Task Tracker — 통합 버전

**프로젝트 기간:** 5주 (W1: 3/24~3/28 ~ W5: 4/21~4/25)
**현재 상태:** W4 통합 테스트 완료 — W5 QA+배포 대기 (2026-04-06)

**서비스 정의:**
> 개인 취향을 반영해 전문가처럼 추천하고, 빠르게 결정하게 만드는 스타일 서비스

**핵심 문서:**
- **기획서:** `ColorFit_상세기획서_v2.md` — 서비스 정의, 시장 분석, 전략(OKR/BSC/SWOT), 심리 설계, KPI
- **PRD:** `PRD.md` — 기능 명세, User Stories, API 스펙, 릴리스 기준
- **디자인:** `DESIGN.md` — 서체, 컬러, 스페이싱, 모션, Card Variants

**사용법:** Claude Code에게 `"Task 3.1v3를 진행해줘"` 처럼 번호로 지시하세요.

---

## 서비스 진화 히스토리

| 버전 | 시기 | 컨셉 | 핵심 변화 |
|------|------|------|----------|
| v1 | 3/24~3/30 | 추천 리스트 (무한스크롤) | 데이터+인프라+스코어링+온보딩 기반 구축 |
| v2 | 3/31 | 결정 대행 (Top1 고정 + 설득) | reason 3파트 구조, 단일 결정 화면, 측정 로직 |
| v3 | 3/31~ | 결정을 쉽게 (Top1 + Explore Top3) | Decision/Explore Mode, 축 기반 다양성, 측정 확장 |

---

## 설계 원칙

1. **Decision Mode가 기본이다.** Top1 + 설득 구조 유지.
2. **Explore Mode는 사용자가 선택한다.** "비슷한 선택 보기" 탭 시에만 확장.
3. **Top3까지 기본, Top5 최대.** Top10 이상 금지.
4. **Top3는 서로 다른 이유를 가진다.** 같은 이유의 코디 나열 금지.
5. **CTA → 설문 → 이동 흐름 유지.** handleDecide / completeSurvey 구조 변경 금지.

---

## 심리 설계 매핑

| 심리 원리 | 적용 위치 | 구현 |
|-----------|----------|------|
| 선택 피로 감소 | Decision Mode | Top1만 노출, 비교 없이 결정 가능 |
| 손실 회피 대응 | risk_guard | "이 조합은 실패 가능성이 낮다" |
| 후회 최소화 | Explore Mode | "다른 선택지도 확인했다"는 심리적 안전 |
| 비교 기반 확신 | Top3 카드 | 각 카드에 차별화된 evidence → "이게 가장 낫다" 확인 |

---

## W1: 데이터 + 인프라 (3/24~3/28) ✅

> 전체 완료 (2026-03-30)

### Lane A: 데이터 파이프라인

| Task | 내용 | 상태 |
|------|------|------|
| 1.1 | 12톤 팔레트 JSON 생성 (300개 색상) | ✅ 3/30 |
| 1.2 | 브랜드 화이트리스트 JSON (120개+) | ✅ 3/30 |
| 1.3 | 네이버 쇼핑 API 수집 스크립트 | ✅ 3/30 |
| 1.4 | 톤별 수집 키워드 설계 (314개 쿼리) | ✅ 3/30 |
| 1.5 | 상품 수집 실행 (83,842개 달성) | ✅ 3/30 |
| 1.6 | 전처리: 상품 정규화 | ✅ 3/30 |
| 1.7 | 전처리: 이미지 색상 추출 + 톤 매핑 | ✅ 3/30 |
| 1.8 | 전처리: 하이브리드 카테고리 분류 | ✅ 3/30 |
| 1.9 | 코디 레시피 JSON 정의 (TPO 8종 x 성별) | ✅ 3/30 |
| 1.10 | 코디 조합 생성 알고리즘 | ✅ 3/30 |
| 1.11 | Gemini 코디 품질 평가 | ✅ 3/30 |

### Lane B: 인프라 셋업

| Task | 내용 | 상태 |
|------|------|------|
| 1.12 | Next.js 15 프로젝트 초기화 | ✅ 3/30 |
| 1.13 | 프론트엔드 디자인 토큰 세팅 | ✅ 3/30 |
| 1.14 | FastAPI 프로젝트 초기화 | ✅ 3/30 |
| 1.15 | DB 스키마 적용 (SQLAlchemy 6 테이블) | ✅ 3/30 |
| 1.16 | 배포 설정 (Vercel + Railway) | ✅ 3/30 |

---

## W2: 추천 엔진 + 온보딩 + 결정 UI (3/31~4/4) ✅

> 전체 완료 (2026-03-31)

### Lane A: 스코어링 (v1)

| Task | 내용 | 상태 |
|------|------|------|
| 2.1 | PCF 스코어링 (퍼스널컬러 적합도) — 19개 테스트 | ✅ 3/30 |
| 2.2 | OF 스코어링 (TPO 적합도) — 17개 테스트 | ✅ 3/30 |
| 2.3 | CH 스코어링 (색상 조화) — 15개 테스트 | ✅ 3/30 |
| 2.4 | PE 스코어링 (가격 효율) — 16개 테스트 | ✅ 3/30 |
| 2.5 | SF 스코어링 (스타일 적합도) — 23개 테스트 | ✅ 3/30 |
| 2.6 | 스타일 호환성 데이터 파일 (227개 궁합) | ✅ 3/30 |

### Lane B: 필터 + 파이프라인 + API (v1)

| Task | 내용 | 상태 |
|------|------|------|
| 2.7 | StyleFilter 규칙 기반 사전 필터 — 13개 테스트 | ✅ 3/30 |
| 2.8 | Hard Filter 8단계 체인 — 31개 테스트 | ✅ 3/30 |
| 2.9 | Soft Score + 리랭킹 — 18개 테스트 | ✅ 3/30 |
| 2.10 | 추천 이유 생성 — 17개 테스트 | ✅ 3/30 |
| 2.11 | Feed/Outfit API 엔드포인트 — 10개 테스트 | ✅ 3/30 |
| 2.12 | 스코어 프리컴퓨팅 (1670개 코디) | ✅ 3/30 |

### Lane C: 온보딩 + 피드 UI (v1)

| Task | 내용 | 상태 |
|------|------|------|
| 2.13 | 온보딩 공통 레이아웃 (진행바 + 전환 모션) | ✅ 3/31 |
| 2.14 | Step 1: 성별 선택 | ✅ 3/31 |
| 2.15 | Step 2: 퍼스널컬러 선택 | ✅ 3/31 |
| 2.16 | Step 3: TPO + 무드 선택 | ✅ 3/31 |
| 2.17 | Step 4: 예산 설정 | ✅ 3/31 |
| 2.18 | Step 5: 비주얼 취향 분석 | ✅ 3/31 |
| 2.19 | 온보딩 API 연동 | ✅ 3/31 |
| 2.20 | 코디 카드 컴포넌트 | ✅ 3/31 |
| 2.21 | 코디 피드 화면 (무한 스크롤) | ✅ 3/31 |
| 2.22 | save/dislike 인터랙션 | ✅ 3/31 |
| 2.23 | 코디 상세 화면 | ✅ 3/31 |
| 2.24 | 하단 탭바 (4탭) | ✅ 3/31 |

### Lane D: v2 결정 구조 전환

| Task | 내용 | 상태 |
|------|------|------|
| 2.10v2 | reason_generator 3파트 구조 (core/evidence/risk_guard) — 33개 테스트 | ✅ 3/31 |
| 2.11v2 | Feed API + Schema 연쇄 수정 (ReasonResponse) | ✅ 3/31 |
| 2.20v2 | OutfitCard → DecisionCard 구조 변경 | ✅ 3/31 |
| 2.21v2 | 피드 → 단일 결정 화면 전환 (page_size=1) | ✅ 3/31 |
| 2.23v2 | 코디 상세 화면 이유 구조 반영 | ✅ 3/31 |

---

## W3: Explore Mode + 품질 강화 (4/1~4/11)

### Lane A: v3 Explore Mode ✅

**Task 3.1v3 — Decision Mode + Explore Mode + Top3 선발** ✅ `2026-03-31`
- **수정 파일:** `frontend/app/feed/page.tsx`
- [x] `page_size=5` 요청 → `selectDiverseTop3()` 축 기반 선발
- [x] Top1: 총점 1위 / Top2: 다른 1순위 축 / Top3: 또 다른 축
- [x] `expandLevel` 상태: 0=Decision, 1=Explore(Top3)
- [x] "비슷한 선택 보기" 보조 CTA + compact 카드 탭 → Decision 복귀
- [x] handleDecide / completeSurvey 구조 **변경 없음**

**Task 3.2v3 — OutfitCard compact variant + 라벨** ✅ `2026-03-31`
- **수정 파일:** `frontend/components/OutfitCard.tsx`
- [x] `variant` prop: `"full"` | `"compact"` (가로 썸네일 80x100)
- [x] `label` prop: 축 라벨 필 뱃지 (Marsala bg)
- [x] `onTap` prop: compact 카드 탭 시 호출
- [x] DESIGN.md 준수: Surface bg, rounded-lg(8px)

**Task 3.3v3 — 측정 필드 확장** ✅ `2026-03-31`
- **수정 파일:** `frontend/lib/api.ts`, `frontend/app/feed/page.tsx`
- [x] `MetricsPayload`에 `expanded`, `expand_level`, `selected_rank` 추가
- [x] CSV export 컬럼 8개 + Debug Panel 표시

### Lane B: 측정 로직 (v2) ✅

**Task 3.8v2 — TTD/CTR/신뢰도/확신 측정 로직** ✅ `2026-03-31`
- **수정 파일:** `frontend/app/feed/page.tsx`, `frontend/lib/api.ts`, `backend/app/routers/metrics.py`
- [x] TTD 계산 (page_view_ts → decision_click_ts)
- [x] 신뢰도 설문 (1~5점) + 실행 확신 설문 (Yes/No)
- [x] POST /api/metrics → JSONL + localStorage 이중 저장
- [x] 설문 후 외부 이동 (window.open)

### Lane C: 배포 + 인프라 안정화 ✅

**Task 3.4 — 프로덕션 배포 안정화** ✅ `2026-04-02`
- [x] Railway 배포 설정 (루트 requirements.txt, start command)
- [x] CORS 설정: Vercel 도메인 추가 → 최종 allow_origins=* (MVP)
- [x] React hydration error #418 수정 (localStorage 클라이언트 마운트 후 읽기)
- [x] 이미지 referrer 차단 해결 (no-referrer 메타태그 + img 속성)
- [x] _hex_to_rgb 빈 color_hex 방어 처리
- 관련 커밋: `9f3e0a0`, `8d17414`, `fae60c9`, `b4f7a5f`, `636bf85`

### Lane D: 데이터 품질 개선 ✅

**Task 3.5 — 데이터 클렌징 + 보강** ✅ `2026-04-04`
- [x] 상품 카테고리 오분류 318건 수정 + 위반 코디 132건 제거
- [x] 상품명 키워드 블랙리스트 추가 (면접/출근/운동 부적합 38건)
- [x] 면접 금기 강화 — 원피스 카테고리 + 데님/미니/플레어 키워드
- [x] 면접 부적합 데이터 직접 정리 (데님/벨벳/원피스/윈드브레이커 등 23건)
- [x] 시즌태그 100% 보강, workout 50개 추가, color_hex 100% 보강
- [x] 4단계 파이프라인 개선 (시즌정제 + OF변별력 + QA게이트 + 앵커유사도)
- 관련 커밋: `06f6447`, `7d79714`, `d11b197`, `097a04d`, `fb6b7db`, `e30abd4`, `c21b66a`

### Lane E: UI 개선 ✅

**Task 3.6 — 프론트엔드 UI 개선** ✅ `2026-04-04`
- [x] 멀티아이템 표시 (코디 카드에 구성 아이템 노출)
- [x] 탭바 4탭 → 2탭 축소 (홈 + 마이)
- [x] 텍스트 차별화 (evidence/risk_guard 표현 개선)
- [x] Step 5 취향 분석 이미지 16장 추가 (네이버 API 크롤링)
- [x] 서비스 신뢰도 보장 — TPO 특화 문구 + UI P0/P1 수정
- 관련 커밋: `d7b9d1f`, `3e91953`, `378f72c`, `67783b4`

### Lane F: 스타일링 엔진 ✅

**Task 3.7 — 스타일링 엔진 + 품질 필터** ✅ `2026-04-06`
- [x] 3단계 품질 필터 시스템 (비의류 필터 / 브랜드 등급 / 연령 키워드)
- [x] 스타일링 엔진 v1: 템플릿 기반 코디 생성 + Top3 조합 다양성
- [x] 스타일링 엔진 v2: 품질 점수 기반 코디 생성
- [x] 스타일링 엔진 v3: style_tag 기반 코디 생성 + Top3 스타일 다양성
- [x] TPO 대표 스타일 보너스 — Top1이 TPO 대표 무드를 반영
- **수정 파일:** `backend/app/services/quality_filters.py`, `backend/app/services/feed_builder.py`, `backend/scripts/generate_styled_outfits.py`
- 관련 커밋: `dbbd7a7`, `702ab42`, `18f0fbf`, `33681c5`, `c066dc5`

### Lane G: 기획서 강화 + PRD ✅

**Task 3.9 — 기획서 전략 프레임워크 강화 + PRD 작성** ✅ `2026-04-06`
- [x] 기획서에 Strategy Framework 적용 (Vision/Mission, OKR 3O+9KR, BSC 4관점 11KPI, SWOT 5+5+4+4, TOWS 8전략)
- [x] 기획서에 Market Research 적용 (TAM/SAM/SOM Top-Down+Bottom-Up 교차검증, Porter's 5 Forces)
- [x] 기획서에 Risk Register 적용 (RBS 4카테고리, 5x5 매트릭스, 10개 리스크+KRI, 히트맵, EMV, 모니터링)
- [x] 소비자 세그멘테이션 4개 + JTBD 고객 여정 맵 추가
- [x] PRD 작성: User Stories 5개, 기능 명세 (F1~F5), API 스펙, 화면 명세, 비기능 요구사항, 릴리스 체크리스트
- **산출물:** `ColorFit_상세기획서_v2.md`, `PRD.md`

### Lane H: 프론트엔드 UI 리파인 ✅

**Task 3.8 — 온보딩 + 피드 UI 리파인** ✅ `2026-04-06`
- **수정 파일:**
  - `frontend/app/onboarding/layout.tsx` — 진행바 + 스텝 카운터 + 슬라이드 모션
  - `frontend/app/onboarding/step1/page.tsx` — 그라디언트 카드 + Marsala 선택 상태 + 스태거 애니메이션
  - `frontend/app/onboarding/step5/page.tsx` — 4라운드 이미지 선택 + 라운드 인디케이터 + 완료 토스트
  - `frontend/app/feed/page.tsx` — Decision/Explore Mode + 설문 바텀시트 + 측정 로직
  - `frontend/app/globals.css` — DESIGN.md 토큰 시스템 (컬러, 스페이싱, CTA, 카드)
  - `frontend/components/BottomTabBar.tsx` — 2탭 (홈+마이) + 글래스모피즘 + spring 애니메이션
  - `frontend/app/demo/page.tsx` — iPhone 14 Pro 프레임 데모 페이지
  - `frontend/package.json` — vitest + @vitejs/plugin-react 추가
- **검증:** npm run build 성공 (13개 페이지), DESIGN.md 전항목 준수, PRD US-1~4 수용기준 충족

### W3 완료 기준
- [x] Decision Mode에서 "비슷한 선택 보기" 버튼 동작 (Task 3.1v3)
- [x] Explore Mode에서 축 기반 Top3 카드 표시 + 선택 복귀 (Task 3.2v3)
- [x] 측정 데이터에 expanded/expand_level/selected_rank 포함 (Task 3.3v3)
- [x] 프로덕션 배포 안정화 (Task 3.4)
- [x] 데이터 품질 + 스타일링 엔진 완료 (Task 3.5~3.7)
- [x] 기획서 강화 + PRD 작성 (Task 3.9)
- [x] 프론트엔드 UI 리파인 완료 (Task 3.8)

---

## W4: 통합 테스트 (4/14~4/18)

**Task 4.1v3 — 전체 흐름 통합 테스트** ✅ `2026-04-06`
- **목적:** Decision Mode + Explore Mode 전체 E2E 검증
- **수정 파일:** `backend/tests/test_integration.py` (신규), `backend/tests/test_scoring_of.py` (수정)
- **작업 내용:**
  - [x] **시나리오 1~5:** PRD US-2~3 수용 기준 기반 — 프론트엔드 vitest 24개 테스트 통과 (selectDiverseTop3 포함)
  - [x] **Edge Case:** 빈 배열, 단일 코디, 동일 축 fallback, null scores — vitest에서 커버
  - [x] **백엔드 통합 테스트 (23개):**
    - Feed API page_size=1/3/5 응답 정상 (TestFeedAPIPageSize)
    - 응답 구조 검증: scores 5축, reasons 3파트, items 배열, 총점 내림차순 (TestFeedAPIResponse)
    - TPO 8종 전체 정상 응답 (TestFeedAPITPO, parametrize)
    - 극단 예산 + 남성 필터 엣지케이스 (TestFeedAPIEdgeCases)
    - reason evidence 다양성 + 내용 비어있지 않음 (TestReasonDiversity)
    - Metrics API: 일반/Decision Mode/설문 스킵 3종 (TestMetricsAPI)
  - [x] **OF 스코어링 테스트 수정:** 3단계 로직(직접100/동의어85/그룹65/불일치30) 반영
- **테스트 결과:**
  - 백엔드 pytest: **272 passed** (기존) + **23 passed** (통합) = 295 전체 통과
  - 프론트엔드 vitest: **24 passed**
- **의존:** W3 전체 완료 ✅

---

## W5: QA + 배포 + 데모 (4/21~4/25)

**Task 5.1v3 — 반응형 QA**
- **수정 파일:** 프론트엔드 전반
- **작업 내용:**
  - [ ] 모바일 (375px): Decision Mode + Explore Mode 전체 확인
  - [ ] compact 카드가 375px에서 깨지지 않는지 확인
  - [ ] "이걸로 결정" CTA 터치 타겟 44px 이상
  - [ ] 설문 바텀시트 모바일 동작
  - [ ] 태블릿 (768px): 레이아웃 확인
- **완료 기준:** 375px, 768px에서 두 모드 모두 정상
- **의존:** Task 4.1v3

**Task 5.3v3 — 성능 최적화**
- **작업 내용:**
  - [ ] Feed API 응답 시간 측정 (page_size=3 기준, 목표 800ms 이내)
  - [ ] Explore Mode 전환 시 추가 로딩 시간 체감 확인
  - [ ] 이미지 lazy loading 확인 (compact 카드 포함)
- **완료 기준:** Feed API 800ms 이내, Explore 전환 체감 1초 이내
- **의존:** Task 5.1v3

**Task 5.4v3 — 버그 수정**
- **작업 내용:**
  - [ ] W3~W4에서 발견된 버그 수정
  - [ ] 크로스 브라우저 테스트 (Chrome, Safari)
- **완료 기준:** Decision/Explore 흐름에 blocking 버그 없음
- **의존:** Task 4.1v3

**Task 5.5v3 — 프로덕션 배포**
- **작업 내용:**
  - [ ] 프론트엔드 프로덕션 빌드 + Vercel 배포
  - [ ] 백엔드 프로덕션 설정 + Railway 배포
  - [ ] 프로덕션 URL 접속 확인
- **완료 기준:** 프로덕션 URL에서 Decision + Explore 모두 동작
- **의존:** Task 5.4v3

**Task 5.6v3 — 데모 준비**
- **작업 내용:**
  - [ ] 데모 시나리오 작성:
    - A: 출근 코디 즉시 결정 (Decision Mode, TTD < 15초)
    - B: 데이트 코디 비교 후 결정 (Explore Mode → Top2 선택)
    - C: TPO 변경 → 재결정
  - [ ] KPI 대시보드: CSV 기반 분석 결과 준비
    - Decision Mode vs Explore Mode TTD 비교
    - expanded 비율
    - selected_rank 분포
  - [ ] 발표 자료 작성
- **완료 기준:** 데모 시나리오 3개 동작 확인, KPI 비교 수치 제시 가능
- **의존:** Task 5.5v3

**Task 5.7v3 — 사용자 검증 테스트** (기획서 13.2 / PRD US-5)
- **목적:** 가설 H1~H5 검증을 위한 실제 사용자 테스트
- **작업 내용:**
  - [ ] 테스트 참여자 모집: 진단러 10명 + 효율러 10명 = 20명
  - [ ] 테스트 가이드 문서 작성 (사용 시나리오, 설문 안내)
  - [ ] 1주간 자유 사용 기간 운영
  - [ ] CSV export로 측정 데이터 추출
  - [ ] 가설별 검증 리포트 작성:
    - H1: ttd_ms(expanded=false) 중앙값 < 15초?
    - H2: trust_score 평균 ≥ 4.0?
    - H3: expanded=true의 trust > expanded=false?
    - H4: selected_rank=1 비율 ≥ 60%?
    - H5: confidence="yes" 비율 ≥ 70%?
  - [ ] 정성 피드백 수집 + 개선점 정리
- **완료 기준:**
  - 20명 참여 완료
  - 5개 가설 각각 성공/실패 판정
  - 검증 리포트 작성
- **의존:** Task 5.5v3

### W5 완료 기준
- [ ] 프로덕션 URL 접속 가능 (Task 5.5v3)
- [ ] Decision + Explore 흐름 버그 없음 (Task 5.4v3)
- [ ] 데모 준비 완료 (Task 5.6v3)
- [ ] Decision Mode TTD < 15초 (Task 5.3v3)
- [ ] 사용자 검증 테스트 착수 (Task 5.7v3)

---

## MVP 핵심 지표 (W5 기준)

| 지표 | 정의 | 목표 |
|------|------|------|
| TTD (Decision Mode) | 피드 진입 → "이걸로 결정" (확장 없이) | < 15초 |
| TTD (Explore Mode) | 피드 진입 → 확장 → 선택 → 결정 | < 30초 |
| CTR | "이걸로 결정" 클릭 / 세션 | > 30% |
| Explore 진입율 | "비슷한 선택 보기" 클릭 / 세션 | 측정 (목표 미설정) |
| 신뢰도 | 설문 1~5점 | 평균 ≥ 4.0 |
| 실행 확신 | Yes 비율 | ≥ 70% |
| 온보딩 완주율 | 진단 시작 → 완료 | ≥ 60% |
| Top1 선택율 | selected_rank=1 비율 | 측정 (검증 목적) |

---

## Fallback 순서

밀릴 경우 아래 순서로 미룸:
1. Top5 확장 (expandLevel=2) — Top3까지만 유지
2. compact 카드 차별화 UI — 리스트 형태로 단순화
3. 프로필/마이페이지 — 홈 화면만으로 동작
4. 반응형 QA 태블릿 — 모바일만 확인

**절대 미루지 않는 것:**
Decision Mode (Top1 + 설득) → "비슷한 선택 보기" → Top3 Explore → 측정 확장

---

## 미구현 (v1/v2에서 Fallback된 항목)

> 아래 항목은 v2 피벗 시 스코프에서 제외됨. 필요 시 W5 이후 별도 진행.

- Task 2.24v2 — 하단 탭바 축소 (4→2탭) → Task 3.6에서 완료
- Task 3.5v2 — 프로필/마이페이지 (간소화)
- Task 3.1~3.4 (v1) — 유사 상품 매칭 + 가격비교 + 아이템 상세
- Task 3.6~3.7 (v1) — 톤 설명 화면 + 취향 관리 화면
- Task 4.1~4.2 (v1) — Top Pick + A vs B 비교
- Task 4.3~4.9 (v1) — 저장 목록, 로그인, 피드백 개인화 학습
- Task 5.2 (v1) — 다크모드
