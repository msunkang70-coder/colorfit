# ColorFit Task Tracker v2 — "결정 + 설득 + 리스크 제거" MVP

**프로젝트 기간:** 5주 (W1: 3/24~3/28 ~ W5: 4/21~4/25)
**현재 상태:** W2-v2 구현 진행 중 (2026-03-31)
**전환 기준:** v1 "추천 리스트" → v2 "결정 + 설득 + 리스크 제거"

**사용법:** Claude Code에게 `"Task 2.10v2를 진행해줘"` 처럼 번호로 지시하세요.

---

## 전환 핵심 원칙

1. **코디 1개만 제시한다.** 리스트/무한스크롤 금지.
2. **왜 이 코디인지 설명한다.** (evidence)
3. **왜 실패하지 않는지 설명한다.** (risk_guard)
4. **사용자가 빠르게 결정하는지 측정한다.** (TTD < 15초)

---

## 병렬 실행 맵

```
W2-v2 ─── 🅐 Task 2.10v2~2.11v2 (백엔드)  ┐ 동시 실행 OK
          🅑 Task 2.20v2~2.24v2 (프론트)    ┘
          ※ 🅑의 2.20v2는 🅐의 2.10v2 완료 후 시작 권장 (스키마 변경)

W3-v2 ─── 🅐 Task 3.5v2 (프론트)           ┐ 동시 실행 OK
          🅑 Task 3.8v2 (측정 로직)         ┘

W4-v2 ─── 🅐 Task 4.10v2 (통합 테스트)      ← 단독

W5-v2 ─── 단독 실행 (QA + 배포 + 데모)
```

**TASK.md 동기화 규칙:**
- 🅐 터미널만 TASK_v2.md를 직접 업데이트
- 🅑 터미널은 완료 시 "Task X.Xv2 끝났어"라고 알려주기만 함
- 사람이 🅑 결과를 확인 후 TASK_v2.md에 수동 체크

---

## W1: 데이터 + 인프라 (3/24~3/28) — v1과 동일, 전부 완료

> W1 Task 1.1~1.16은 v1 TASK.md 그대로 유지. 변경 없음.
> 모든 Task 완료됨 (1.16 배포 일부 미완).

---

## W2-v2: 이유 구조 전환 + 결정 UI (3/31~4/4)

> v1의 W2 중 스코어링(2.1~2.9), 온보딩(2.13~2.19)은 완료됨. 그대로 유지.
> 아래는 **방향 변경이 필요한 Task만** 재정의한다.

### 🅐 Lane A: 백엔드 — 이유 구조 전환

**Task 2.10v2 — reason_generator 3파트 구조 전환** ✅ `2026-03-31`
- **목적:** 템플릿 결론형 이유를 "core + evidence + risk_guard" 구조로 전환
- **수정 파일:** `backend/app/services/reason_generator.py`
- **작업 내용:**
  - [x] `ReasonResult` TypedDict 정의 (`core: str`, `evidence: list[str]`, `risk_guard: list[str]`)
  - [x] `generate_reasons()` 시그니처 변경: `items: list[dict]` 파라미터 추가, 반환 → `ReasonResult`
  - [x] `_build_core()` 구현: 아이템명 + 톤 + TPO 조립
  - [x] `_build_evidence()` 구현: 1순위 축 + 아이템 데이터 기반 인과 문장
  - [x] `_build_risk_guard()` 구현: 5패턴 (명도 대비/포멀도 일관/TPO 범위/스타일/가격)
  - [x] 기존 `TEMPLATES` dict 및 템플릿 치환 로직 제거
  - [x] `_particle()` 한글 조사 처리 헬퍼 추가
  - [x] pytest 테스트 재작성 — 33개 통과
- **완료 기준:** ✅ 모두 충족
- **의존:** 없음 (독립 실행 가능)

**Task 2.11v2 — Feed API + Schema 연쇄 수정** ✅ `2026-03-31`
- **목적:** 새 이유 구조를 API 응답에 반영
- **수정 파일:**
  - `backend/app/schemas/outfit.py`
  - `backend/app/routers/feed.py`
  - `backend/app/routers/outfit.py`
- **작업 내용:**
  - [x] `ReasonResponse` Pydantic 모델 추가
  - [x] `OutfitResponse.reasons` 타입 변경: `list[str]` → `ReasonResponse | None`
  - [x] `feed.py`: `generate_reasons()` 호출 시 `items` 데이터 전달
  - [x] `feed.py`: `_outfit_to_response()`에서 `ReasonResult` → `ReasonResponse` 변환
  - [x] `outfit.py` (라우터): 단건 조회에서도 이유 생성 + tone_id/tpo 파라미터 추가
  - [x] `FeedResponse` 호환성 확인
- **완료 기준:** ✅ 모두 충족
- **의존:** Task 2.10v2

### 🅑 Lane B: 프론트엔드 — 결정 UI 전환

**Task 2.20v2 — OutfitCard → DecisionCard 구조 변경** ✅ `2026-03-31`
- **목적:** 추천 카드를 결정 카드로 전환 (이유 3파트 표시)
- **수정 파일:** `frontend/components/OutfitCard.tsx`
- **작업 내용:**
  - [x] Props interface 변경: `reasons: { core, evidence[], risk_guard[] } | null`
  - [x] 카드 레이아웃: core(제목) + 가격 + evidence[0] + risk_guard[0]
  - [x] 기존 title/reason/scores prop 제거
  - [x] 스코어 뱃지 제거
  - [x] risk_guard에 성공 컬러 (#6B7F5E) 적용
- **완료 기준:** ✅ 모두 충족
- **의존:** Task 2.11v2

**Task 2.21v2 — 피드 → 단일 결정 화면 전환** ✅ `2026-03-31`
- **목적:** 무한스크롤 피드를 "코디 1개 전체화면" 구조로 전환
- **수정 파일:** `frontend/app/feed/page.tsx`
- **작업 내용:**
  - [x] `page_size` 변경: `"20"` → `"1"`
  - [x] IntersectionObserver 기반 무한스크롤 제거
  - [x] 코디 1개만 표시 (decision state)
  - [x] "오늘의 결정" 헤더 + 결정 카드 + evidence/risk_guard 확장 영역
  - [x] CTA: "이걸로 결정" (Marsala, 풀와이드, 하단 고정)
  - [x] "다른 제안 보기" 텍스트 버튼
  - [x] TPO 탭 유지
  - [x] 예산 슬라이더 유지
  - [x] TTD 측정 로직 (performance.now + localStorage)
  - [x] FeedOutfit interface 변경: ReasonData 구조체
  - [x] loading/empty/error 4상태 유지
- **완료 기준:** ✅ 모두 충족
- **의존:** Task 2.20v2

**Task 2.23v2 — 코디 상세 화면 이유 구조 반영** ✅ `2026-03-31`
- **목적:** 상세 화면의 이유 표시를 3파트 구조로 변경
- **수정 파일:** `frontend/app/outfit/[id]/page.tsx`
- **작업 내용:**
  - [x] "왜 이 코디인가요?" 섹션 (evidence, #964F4C 헤더)
  - [x] "이거 입어도 괜찮을까요?" 섹션 (risk_guard, #6B7F5E 헤더)
  - [x] 5축 스코어 바 차트 제거
  - [x] 하단 CTA: "이걸로 결정" 단일 버튼
  - [x] reasons 타입 변경: `ReasonData | null`
- **완료 기준:** ✅ 모두 충족
- **의존:** Task 2.11v2

**Task 2.24v2 — 하단 탭바 축소**
- **목적:** MVP에 불필요한 탭 제거
- **수정 파일:** `frontend/components/BottomTabBar.tsx`
- **작업 내용:**
  - [ ] 4탭 → 2탭: **홈**(피드) + **마이**(프로필)
  - [ ] 저장 탭, Top 탭 제거
  - [ ] 기존 /saved, /top-pick 페이지 placeholder 유지 (라우팅만 제거)
- **완료 기준:**
  - 탭바에 홈 / 마이 2개만 표시
  - 탭 전환 동작
- **의존:** 없음

### W2-v2 완료 기준 ✅
- [x] `generate_reasons()`가 core/evidence/risk_guard 반환 (Task 2.10v2)
- [x] API 응답에 3파트 이유 포함 (Task 2.11v2)
- [x] 피드 화면에 코디 1개 + 이유 + "이걸로 결정" CTA (Task 2.21v2)
- [x] 상세 화면 비활성화, 피드 단일 결정 UX 완성 (Task 2.23v2)

---

## W3-v2: 측정 + 프로필 (4/7~4/11)

### 🅐 프론트엔드

**Task 3.5v2 — 프로필/마이페이지 (간소화)**
- **목적:** 톤 정보 확인 + 설정 변경만 제공
- **수정 파일:** `frontend/app/profile/page.tsx`
- **작업 내용:**
  - [ ] 톤 카드 (그라데이션 배경 + 톤 이름, Nanum Myeongjo 28px)
  - [ ] 잘 어울리는 색 스와치 6개
  - [ ] 내 정보 (성별, TPO, 예산) + "변경" 버튼 → 해당 온보딩 Step 재진행
  - [ ] 취향 관리, 학습 상태 등 제외
- **완료 기준:**
  - 톤 카드 표시
  - 설정 변경 동작
- **의존:** 없음

### 🅑 측정 로직

**Task 3.8v2 — TTD/CTR/신뢰도/확신 측정 로직** ✅ `2026-03-31`
- **목적:** MVP 핵심 KPI 측정 코드 삽입
- **수정 파일:**
  - `frontend/app/feed/page.tsx`
  - `frontend/lib/api.ts`
  - `backend/app/routers/metrics.py` (신규)
  - `backend/app/main.py`
- **작업 내용:**
  - [x] **page_view_ts**: ISO 타임스탬프로 피드 진입 시점 기록
  - [x] **decision_click_ts**: CTA 클릭 시점 ISO 타임스탬프 기록
  - [x] **TTD 계산**: decision_click_ts - page_view_ts (ms)
  - [x] **CTR**: cta_clicked boolean 기록으로 세션별 집계 가능
  - [x] **신뢰도 설문**: CTA 후 바텀시트 팝업, 1~5점 탭 선택
  - [x] **실행 확신 설문**: 네/아니요 2버튼
  - [x] **스킵 가능**: 건너뛰기 버튼 + 배경 탭으로 스킵
  - [x] **백엔드 전송**: POST /api/metrics → JSONL 파일 저장
  - [x] **이중 저장**: 서버 전송 + localStorage 동시 저장 (누락 방지)
  - [x] **설문 후 외부 이동**: 제출/스킵 완료 후 window.open
- **완료 기준:** ✅ 모두 충족
- **의존:** Task 2.21v2

### W3-v2 완료 기준
- [ ] 프로필 페이지 동작 (Task 3.5v2)
- [x] TTD/CTR 측정 동작 (Task 3.8v2) ✅
- [x] 신뢰도/확신 설문 동작 (Task 3.8v2) ✅

---

## W4-v2: 통합 테스트 (4/14~4/18)

**Task 4.10v2 — 결정 흐름 통합 테스트**
- **목적:** 전체 결정 흐름 E2E 검증
- **수정 파일:** 테스트 파일 (신규 또는 기존 수정)
- **작업 내용:**
  - [ ] **시나리오 1: 첫 사용자 결정 흐름**
    - 온보딩 5단계 → 피드 진입 → 코디 1개 표시 → "이걸로 결정" → 설문 → 외부 링크
  - [ ] **시나리오 2: TPO 변경 결정**
    - 피드에서 TPO 탭 변경 → 새 코디 1개 표시 → evidence/risk_guard 확인 → 결정
  - [ ] **시나리오 3: "다른 결정 보기"**
    - "다른 결정 보기" 탭 → 새 코디 로드 → 이전 코디와 다른 코디 확인
  - [ ] **Edge Case:**
    - 코디 0개 결과 (필터 조건 극단) → empty state
    - 이유 생성 실패 (scores 누락) → fallback 텍스트
    - 예산 초과 필터 → 결과 없음 처리
  - [ ] **백엔드 단위 테스트:**
    - reason_generator: core/evidence/risk_guard 각 파트 정상 생성
    - feed API: page_size=1 응답 정상
    - 아이템 데이터 누락 시 fallback 동작
- **완료 기준:**
  - 3개 시나리오 수동 테스트 통과
  - Edge case 3개 통과
  - 백엔드 pytest 전체 통과
- **의존:** W2-v2 + W3-v2 전체 완료

---

## W5-v2: QA + 배포 + 데모 (4/21~4/25)

**Task 5.1v2 — 반응형 QA (결정 화면 중심)**
- **목적:** 결정 화면이 모든 뷰포트에서 동작하는지 확인
- **수정 파일:** 프론트엔드 전반
- **작업 내용:**
  - [ ] 모바일 (375px): 결정 화면 + 온보딩 전체 확인
  - [ ] 태블릿 (768px): 레이아웃 확인
  - [ ] "이걸로 결정" CTA 터치 타겟 44px 이상
  - [ ] evidence/risk_guard 텍스트 줄바꿈 정상
  - [ ] 설문 바텀시트 모바일 동작
- **완료 기준:**
  - 375px, 768px에서 결정 화면 정상
  - CTA 터치 타겟 확보
- **의존:** Task 4.10v2

**Task 5.3v2 — 성능 최적화 (TTD 중심)**
- **목적:** TTD 15초 이내 달성을 위한 성능 확보
- **수정 파일:** 프론트/백엔드
- **작업 내용:**
  - [ ] Feed API 응답 시간 측정 (page_size=1 기준, 목표 500ms 이내)
  - [ ] 코디 이미지 lazy loading 확인
  - [ ] 불필요한 리렌더링 제거
  - [ ] Lighthouse 성능 점수 확인 (목표: 80+)
- **완료 기준:**
  - Feed API 500ms 이내
  - TTD 측정값 평균 < 15초 (내부 테스트 기준)
- **의존:** Task 5.1v2

**Task 5.4v2 — 버그 수정**
- **수정 파일:** 발견되는 대로
- **작업 내용:**
  - [ ] W2~W4에서 발견된 버그 목록 정리
  - [ ] 크로스 브라우저 테스트 (Chrome, Safari)
  - [ ] 결정 흐름 중심 버그 우선 수정
- **완료 기준:**
  - 결정 흐름에 blocking 버그 없음
- **의존:** Task 4.10v2

**Task 5.5v2 — 프로덕션 배포**
- **수정 파일:** 배포 설정
- **작업 내용:**
  - [ ] 프론트엔드 프로덕션 빌드 + Vercel 배포
  - [ ] 백엔드 프로덕션 설정 + Railway 배포
  - [ ] 환경변수 확인
  - [ ] 프로덕션 URL 접속 확인
- **완료 기준:**
  - 프로덕션 URL에서 결정 흐름 동작
- **의존:** Task 5.4v2

**Task 5.6v2 — 데모 준비 (결정 서비스 시나리오)**
- **수정 파일:** 발표 자료
- **작업 내용:**
  - [ ] 데모 시나리오 작성:
    - 시나리오 A: 출근 코디 결정 (15초 이내)
    - 시나리오 B: 데이트 코디 결정 (TPO 변경)
  - [ ] 데모용 샘플 데이터 확인 (봄웜라이트 기준)
  - [ ] KPI 대시보드 준비 (localStorage 데이터 시각화 — 간단한 console 출력 또는 별도 페이지)
  - [ ] 발표 자료 작성
- **완료 기준:**
  - 데모 시나리오 2개 동작 확인
  - KPI 수치 제시 가능
- **의존:** Task 5.5v2

### W5-v2 완료 기준
- [ ] 프로덕션 URL 접속 가능 (Task 5.5v2)
- [ ] 결정 흐름 버그 없음 (Task 5.4v2)
- [ ] 데모 준비 완료 (Task 5.6v2)
- [ ] TTD < 15초 달성 (Task 5.3v2)

---

## MVP 핵심 지표 (W5 기준)

| 지표 | 정의 | 목표 |
|------|------|------|
| TTD (Time to Decision) | 피드 진입 → "이걸로 결정" 클릭 | < 15초 |
| CTR (Click-Through Rate) | "이걸로 결정" 클릭 / 세션 | > 30% |
| 신뢰도 (Trust Score) | "이 설명이 납득됐나요?" 1~5점 | 평균 ≥ 4.0 |
| 실행 확신 (Confidence) | "이대로 입어도 되겠다고 느꼈나요?" | Yes ≥ 70% |
| 온보딩 완주율 | 진단 시작 → 완료 | ≥ 60% |

---

## Fallback 순서 (W3-v2 금요일 판단)

밀릴 경우 아래 순서로 2차 미룸:
1. 프로필/마이페이지 (Task 3.5v2) — 홈 화면만으로 MVP 동작
2. 실행 확신 설문 (Task 3.8v2의 Yes/No) — 신뢰도 설문만 유지
3. 상세 화면 리뉴얼 (Task 2.23v2) — 피드 결정 화면만으로 충분
4. 반응형 QA 태블릿 (Task 5.1v2) — 모바일만 확인

**절대 미루지 않는 것:** reason_generator 3파트 전환 → 단일 결정 화면 → "이걸로 결정" CTA → TTD 측정
