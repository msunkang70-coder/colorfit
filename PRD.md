# ColorFit PRD (Product Requirements Document)

**제품명:** ColorFit (컬러핏)
**버전:** MVP v3
**작성일:** 2026-04-06
**기획서:** `ColorFit_상세기획서_v2.md`
**디자인:** `DESIGN.md`

---

## 1. 제품 개요

### 1.1 한 줄 정의

퍼스널컬러·상황·예산을 분석해 최적 코디 1개를 제안하고, 근거를 설명하고, 원하면 비교 선택지를 제공하여 빠르고 확신 있는 결정을 만드는 모바일 웹 서비스.

### 1.2 타겟 사용자

| 세그먼트 | 우선순위 | 핵심 니즈 |
|----------|---------|----------|
| 진단러 (퍼스널컬러 진단 완료, 활용 못함) | 1순위 | "내 톤에 맞는 코디를 골라줘" |
| 효율러 (결정 피로 높은 직장인) | 2순위 | "빠르게 정해주되 근거 있게" |

### 1.3 성공 지표

| 지표 | 목표 | 가설 |
|------|------|------|
| TTD (Decision Mode) | < 15초 | H1 |
| 신뢰도 설문 | 평균 ≥ 4.0 | H2 |
| 실행 확신 Yes | ≥ 70% | H5 |
| CTR | > 30% | - |
| 온보딩 완주율 | ≥ 60% | - |

---

## 2. User Stories

### US-1: 온보딩

```
AS A 퍼스널컬러 진단을 받은 사용자
I WANT TO 성별, 톤, TPO, 예산, 취향을 입력하고
SO THAT 나에게 맞는 코디를 추천받을 수 있다
```

**수용 기준:**
- [ ] 5단계 순차 진행 (성별 → 톤 → TPO+무드 → 예산 → 취향)
- [ ] 각 단계에서 "건너뛰기" 가능
- [ ] 상단 진행 바 표시 (현재 단계 / 5)
- [ ] 뒤로가기 시 이전 선택 유지
- [ ] 완료 시 피드 화면으로 전환
- [ ] 입력 데이터 localStorage + API 저장

### US-2: Decision Mode (코디 결정)

```
AS A 코디를 결정하고 싶은 사용자
I WANT TO 최적 코디 1개와 그 이유를 보고
SO THAT 빠르게 확신을 갖고 결정할 수 있다
```

**수용 기준:**
- [ ] Top1 코디 전체 화면 표시 (이미지 3:4 + core + 가격 + evidence + risk_guard)
- [ ] "이걸로 결정" CTA (Marsala, 풀와이드, 하단 고정)
- [ ] TPO 탭 필터 (가로 스크롤 필 버튼)
- [ ] TPO 변경 시 새 코디 로드 + Decision Mode 리셋
- [ ] 코디 0개일 때 empty state 표시
- [ ] 로딩 시 스켈레톤 UI 표시

### US-3: Explore Mode (비교 후 결정)

```
AS A 다른 선택지도 확인하고 싶은 사용자
I WANT TO 축 기반으로 차별화된 Top3를 비교하고
SO THAT "다른 것도 봤다"는 확신을 가지고 결정할 수 있다
```

**수용 기준:**
- [ ] "비슷한 선택 보기" 보조 CTA (코디 2개 이상일 때만 표시)
- [ ] 탭 시 Top2~3 compact 카드 표시 (가로 썸네일 80x100 + 축 라벨 뱃지)
- [ ] 각 compact 카드에 차별화된 축 라벨 ("컬러 매칭형", "상황 최적형" 등)
- [ ] compact 카드 탭 → 해당 코디가 Decision Mode의 Top1 위치로 교체
- [ ] 코디 1개일 때 "비슷한 선택 보기" 숨김
- [ ] Top3 선발: `selectDiverseTop3()` — 축 기반 다양성 보장

### US-4: 설문 + 측정

```
AS A "이걸로 결정"을 탭한 사용자
I WANT TO 간단한 설문에 답하고 쇼핑몰로 이동하고
SO THAT 서비스가 내 결정 경험을 개선할 수 있다
```

**수용 기준:**
- [ ] CTA 탭 → 바텀시트 팝업
- [ ] 신뢰도 설문: "이 코디를 얼마나 신뢰하나요?" 1~5점
- [ ] 실행 확신 설문: "이대로 입을 것 같나요?" Yes/No
- [ ] 건너뛰기 가능 (배경 탭 또는 건너뛰기 버튼)
- [ ] 제출/스킵 후 외부 쇼핑몰 이동 (window.open → fallback location.href)
- [ ] 측정 데이터 전송: localStorage queue 우선 → sendBeacon → fetch(keepalive)

### US-5: 사용자 검증 테스트

```
AS A 프로젝트 오너
I WANT TO 20명의 실제 사용자에게 서비스를 테스트하고
SO THAT 가설 H1~H5를 검증할 수 있다
```

**수용 기준:**
- [ ] 프로덕션 URL에서 전체 흐름 동작 (온보딩 → 피드 → 결정 → 설문 → 이동)
- [ ] CSV export로 측정 데이터 추출 가능
- [ ] 진단러 10명 + 효율러 10명 모집 완료
- [ ] 1주간 자유 사용 후 데이터 수집
- [ ] 가설별 성공/실패 판정 리포트 작성

---

## 3. 기능 명세

### F1: 온보딩 (5단계)

| Step | 화면 | 입력 | 파일 |
|------|------|------|------|
| 1 | 성별 선택 | 여성/남성 카드 탭 | `onboarding/step1/page.tsx` |
| 2 | 퍼스널컬러 선택 | 시즌 스트립 → 톤 칩 탭 | `onboarding/step2/page.tsx` |
| 3 | TPO + 무드 선택 | TPO 필 버튼 (최대 3) + 무드 태그 (최대 5) | `onboarding/step3/page.tsx` |
| 4 | 예산 설정 | 듀얼 썸 슬라이더 + 프리셋 4개 | `onboarding/step4/page.tsx` |
| 5 | 비주얼 취향 | 2x2 이미지 그리드 × 4라운드 | `onboarding/step5/page.tsx` |

**비기능 요구사항:**
- 각 Step 전환: Framer Motion 좌→우 슬라이드 (0.3s)
- 진행 바: Marsala 채움 (currentStep / 5)
- Step 완료 시 자동 다음 Step 전환 (0.5s 딜레이)
- 모든 입력 localStorage 영속화 (새로고침 유지)

### F2: Decision Mode

| 요소 | 스펙 | 디자인 |
|------|------|--------|
| 코디 이미지 | 3:4 비율, rounded-lg, no-referrer | 풀블리드 |
| core | Nanum Myeongjo 16px | 아이템 + 톤 + TPO |
| 가격 | Pretendard 600 | "₩{총합}" |
| evidence | Pretendard 400, 14px | #222222, 1~2줄 |
| risk_guard | Pretendard 400, 14px | #6B7F5E (성공 컬러) |
| CTA | Marsala bg, white text, 풀와이드 | height 52px, 하단 고정 |
| "비슷한 선택 보기" | Ghost 버튼, CTA 위 | 코디 2개+ 시 표시 |
| TPO 탭 | 가로 스크롤 필 버튼 | active=Marsala, inactive=Surface |

**API 호출:** `GET /api/feed?tone_id={}&tpo={}&gender={}&budget_min={}&budget_max={}&page_size=5`

**데이터 흐름:**
1. API에서 5개 코디 수신
2. `selectDiverseTop3()` 실행 → Top1/Top2/Top3 선발
3. Decision Mode: Top1만 렌더링
4. `page_view_ts` 기록 (performance.now)

### F3: Explore Mode

| 요소 | 스펙 | 디자인 |
|------|------|--------|
| Top1 카드 | Full variant + "1위 추천" 라벨 | 상단, 강조 |
| compact 카드 (Top2, Top3) | 80x100 썸네일 + core + 가격 + evidence 1줄 | Surface bg, rounded-lg, 8px padding |
| 축 라벨 뱃지 | Marsala pill, white text, 10px | "컬러 매칭형" / "상황 최적형" 등 |

**Top3 선발 알고리즘 (`selectDiverseTop3`):**
```
입력: outfits (5개, 총점 내림차순)
1. Top1 = outfits[0] (총점 1위)
2. Top1의 1순위 축 확인
3. Top2 = Top1과 다른 1순위 축을 가진 코디 중 총점 최고
4. Top3 = Top1,2와 다른 1순위 축을 가진 코디 중 총점 최고
5. fallback: 축 동일 시 순차 선택
```

**축 → 라벨 매핑:**

| 축 | 라벨 |
|----|------|
| pcf | 컬러 매칭형 |
| of | 상황 최적형 |
| ch | 색감 조화형 |
| pe | 가성비형 |
| sf | 실루엣형 |

**모드 전환:**
- "비슷한 선택 보기" 탭 → `expandLevel = 1`
- compact 카드 탭 → 해당 코디를 `currentOutfit`으로 교체 → `expandLevel = 0`
- TPO 변경 → 새 API 호출 → `expandLevel = 0` 리셋

### F4: 설문 + 측정

**바텀시트 설문 흐름:**
```
CTA "이걸로 결정" 탭
  → 바텀시트 올라옴 (spring 300/30)
  → Q1: 신뢰도 (1~5 탭)
  → Q2: 실행 확신 (Yes/No)
  → 건너뛰기: 아무 때나 (배경 탭 또는 버튼)
  → 완료/스킵 → postMetrics() + window.open(쇼핑몰)
```

**MetricsPayload:**
```typescript
{
  session_id: string
  outfit_id: string
  page_view_ts: string        // ISO
  decision_click_ts: string   // ISO
  ttd_ms: number
  cta_clicked: boolean
  trust_score: number | null  // 1~5
  confidence: string | null   // "yes" | "no" | "skip"
  expanded: boolean
  expand_level: number        // 0 | 1
  selected_rank: number       // 1~5
  tone_id: string
  tpo: string
}
```

**전송 우선순위:**
1. `localStorage` queue 저장 (colorfit_metrics_queue)
2. `navigator.sendBeacon` → `POST /api/metrics`
3. fallback: `fetch(keepalive: true)`
4. queue 최대 100건 FIFO

### F5: TPO 필터

| TPO | 여성 | 남성 |
|-----|------|------|
| 출근 | ✅ | ✅ |
| 데이트 | ✅ | ✅ |
| 캐주얼 | ✅ | ✅ |
| 여행 | ✅ | ✅ |
| 운동 | ✅ | ✅ |
| 면접 | ✅ | ✅ |
| 결혼식 | ✅ | ✅ |
| 모임 | ✅ | ✅ |

---

## 4. 화면 명세

### 4.1 화면 목록

| # | 화면 | 경로 | 파일 | 상태 |
|---|------|------|------|------|
| S1 | 랜딩/리다이렉트 | `/` | `app/page.tsx` | ✅ |
| S2 | 온보딩 Step 1~5 | `/onboarding/step{1-5}` | `app/onboarding/step{N}/page.tsx` | ✅ |
| S3 | 코디 피드 (Decision/Explore) | `/feed` | `app/feed/page.tsx` | ✅ |
| S4 | 코디 상세 | `/outfit/[id]` | `app/outfit/[id]/page.tsx` | ✅ |
| S5 | 데모 | `/demo` | `app/demo/page.tsx` | ✅ |
| S6 | 저장 목록 (placeholder) | `/saved` | `app/saved/page.tsx` | placeholder |
| S7 | 프로필 (placeholder) | `/profile` | `app/profile/page.tsx` | placeholder |

### 4.2 공통 컴포넌트

| 컴포넌트 | 파일 | 역할 |
|----------|------|------|
| OutfitCard | `components/OutfitCard.tsx` | Full/Compact variant, 축 라벨, onTap |
| BottomTabBar | `components/BottomTabBar.tsx` | 홈 + 마이 2탭 |

### 4.3 상태 관리

| 상태 | 위치 | 설명 |
|------|------|------|
| 온보딩 데이터 | localStorage `colorfit_onboarding` | 성별, 톤, TPO, 예산, 취향 |
| 현재 코디 | feed/page.tsx state | `currentOutfit`, `allOutfits`, `top3` |
| Explore 상태 | feed/page.tsx state | `expandLevel` (0/1) |
| 측정 큐 | localStorage `colorfit_metrics_queue` | MetricsPayload[] |
| 세션 | localStorage `colorfit_session_id` | 랜덤 ID |

---

## 5. API 명세

### 5.1 Feed API

```
GET /api/feed
```

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| tone_id | string | Y | 12톤 ID (예: spring_warm_light) |
| tpo | string | Y | TPO (예: commute) |
| gender | string | Y | male / female |
| budget_min | int | N | 예산 하한 (원) |
| budget_max | int | N | 예산 상한 (원) |
| page_size | int | N | 기본 5 |

**응답:**
```json
{
  "outfits": [
    {
      "id": "outfit_sw_001",
      "items": [...],
      "total_price": 77000,
      "scores": { "pcf": 92, "of": 85, "ch": 78, "pe": 70, "sf": 88, "total": 84.3 },
      "reasons": {
        "core": "니트 + 슬랙스 — 봄웜라이트 출근룩",
        "evidence": ["니트의 색감이 봄웜라이트 톤과..."],
        "risk_guard": ["니트와 슬랙스는 색상 대비가..."]
      },
      "image_url": "https://..."
    }
  ],
  "total": 5,
  "tone_id": "spring_warm_light",
  "tpo": "commute"
}
```

### 5.2 Metrics API

```
POST /api/metrics
```

**Body:** MetricsPayload (섹션 F4 참조)
**응답:** `{ "status": "ok" }`
**저장:** JSONL 파일 (`backend/data/metrics.jsonl`)

### 5.3 Onboarding API

```
POST /api/onboarding
```

**Body:**
```json
{
  "gender": "female",
  "tone_id": "summer_cool_soft",
  "tpo_list": ["commute", "date"],
  "mood_tags": ["미니멀", "모던"],
  "budget_min": 30000,
  "budget_max": 100000,
  "style_seeds": [...]
}
```

---

## 6. 비기능 요구사항

### 6.1 성능

| 항목 | 목표 | 측정 |
|------|------|------|
| Feed API 응답 | < 800ms (p95) | 서버 로그 |
| 첫 화면 로드 (FCP) | < 2초 | Lighthouse |
| Explore 전환 | < 1초 (체감) | 프론트에서 이미 로드된 데이터 사용 |
| 이미지 로딩 | lazy loading | `loading="lazy"` |

### 6.2 호환성

| 환경 | 지원 |
|------|------|
| Chrome (모바일/데스크톱) | 필수 |
| Safari (iOS) | 필수 |
| 375px (모바일) | 필수 |
| 768px (태블릿) | 권장 |
| 최대 폭 | 768px (센터 정렬) |

### 6.3 접근성

| 항목 | 기준 |
|------|------|
| CTA 터치 타겟 | 최소 44x44px |
| 이미지 alt | 코디 설명 텍스트 |
| 색상 대비 | Marsala on white ≥ 4.5:1 |
| 모션 | `prefers-reduced-motion` 존중 |

### 6.4 데이터 안정성

| 항목 | 구현 |
|------|------|
| 측정 데이터 | localStorage queue + sendBeacon 이중 저장 |
| 온보딩 데이터 | localStorage 영속화 |
| 서버 로그 | JSONL 파일 + CSV export |

---

## 7. 릴리스 기준

### 7.1 MVP 릴리스 체크리스트

**필수 (Blocking):**
- [ ] 온보딩 5단계 → 피드 진입 동작
- [ ] Decision Mode: Top1 + core/evidence/risk_guard 표시
- [ ] "이걸로 결정" CTA → 설문 → 외부 이동
- [ ] Explore Mode: "비슷한 선택 보기" → Top3 compact 카드
- [ ] compact 카드 탭 → Decision Mode 복귀
- [ ] TPO 탭 변경 → 새 코디 로드
- [ ] 측정 데이터 전송 (TTD/CTR/trust/confidence/expanded/selected_rank)
- [ ] 프로덕션 URL 접속 가능 (Vercel + Railway)

**권장 (Non-blocking):**
- [ ] compact 카드 375px 깨지지 않음
- [ ] CTA 터치 타겟 44px 이상
- [ ] Feed API p95 < 800ms
- [ ] 크로스 브라우저 (Chrome + Safari)

### 7.2 사용자 검증 릴리스 기준

- [ ] 프로덕션 URL 안정 동작 (1일 이상 무장애)
- [ ] CSV export 동작 확인
- [ ] 20명 모집 완료 (진단러 10 + 효율러 10)
- [ ] 테스트 가이드 문서 준비
