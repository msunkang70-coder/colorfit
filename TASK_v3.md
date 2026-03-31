# ColorFit Task Tracker v3 — "결정을 쉽게 만드는 스타일 서비스"

**프로젝트 기간:** 5주 (W1: 3/24~3/28 ~ W5: 4/21~4/25)
**현재 상태:** v3 W3 구현 완료 (2026-03-31)
**전환 기준:** v2 "결정 대행" → v3 "결정을 쉽게 만드는 서비스"

**서비스 정의:**
> 개인 취향을 반영해 전문가처럼 추천하고, 빠르게 결정하게 만드는 스타일 서비스

**사용법:** Claude Code에게 `"Task 3.1v3를 진행해줘"` 처럼 번호로 지시하세요.

---

## v2 → v3 핵심 변화

| 항목 | v2 | v3 |
|------|----|----|
| UX 모델 | Top1 고정, 비교 불가 | Top1 기본 → 사용자 선택 시 Top3 확장 |
| 사용자 역할 | 수락자 (결정을 받는다) | 선택자 (비교 후 결정한다) |
| 심리 설계 | 설득 + 리스크 제거 | 설득 + 비교 확신 + 후회 최소화 |
| CTA | "이걸로 결정" 단일 | "이걸로 결정" + "비슷한 선택 보기" |
| 데이터 | TTD/CTR/신뢰도/확신 | + expanded/expand_level/selected_rank |

---

## 설계 원칙

1. **Decision Mode가 기본이다.** Top1 + 설득 구조 유지.
2. **Explore Mode는 사용자가 선택한다.** "비슷한 선택 보기" 탭 시에만 확장.
3. **Top3까지 기본, Top5 최대.** Top10 이상 금지.
4. **Top3는 서로 다른 이유를 가진다.** 같은 이유의 코디 나열 금지.
5. **API 변경 금지.** 기존 feed API의 page_size 파라미터로 Top-N 요청.
6. **CTA → 설문 → 이동 흐름 유지.** handleDecide / completeSurvey 구조 변경 금지.

---

## 심리 설계 매핑

| 심리 원리 | 적용 위치 | 구현 |
|-----------|----------|------|
| 선택 피로 감소 | Decision Mode | Top1만 노출, 비교 없이 결정 가능 |
| 손실 회피 대응 | risk_guard | "이 조합은 실패 가능성이 낮다" |
| 후회 최소화 | Explore Mode | "다른 선택지도 확인했다"는 심리적 안전 |
| 비교 기반 확신 | Top3 카드 | 각 카드에 차별화된 evidence → "이게 가장 낫다" 확인 |

---

## 병렬 실행 맵

```
W3-v3 ─── 🅐 Task 3.1v3~3.2v3 (프론트 UX)   ┐ 동시 실행 OK
          🅑 Task 3.3v3 (측정 확장)           ┘

W4-v3 ─── 🅐 Task 4.1v3 (통합 테스트)         ← 단독

W5-v3 ─── 단독 실행 (QA + 배포 + 데모)
```

---

## 완료 기준 (v2에서 이관)

> 아래 항목은 v2에서 이미 완료. v3에서 변경하지 않는다.

- [x] W1 전체 (데이터 + 인프라) — v1 완료
- [x] W2 스코어링 (2.1~2.9) + 온보딩 (2.13~2.19) — v1 완료
- [x] reason_generator 3파트 구조 (2.10v2) — v2 완료
- [x] Feed API + Schema (2.11v2) — v2 완료
- [x] OutfitCard 결정 카드 (2.20v2) — v2 완료
- [x] 단일 결정 화면 (2.21v2) — v2 완료
- [x] 측정 로직 + 설문 (3.8v2) — v2 완료
- [x] 측정 안정화: sendBeacon + localStorage queue — v2 완료

---

## W3-v3: Explore Mode + 측정 확장 (4/7~4/11)

### 🅐 Lane A: 프론트엔드 — Explore Mode

**Task 3.1v3 — Decision Mode + Explore Mode + Top3 선발** ✅ `2026-03-31`
- **목적:** page_size=5 요청 → 축 기반 Top3 재선발 → Decision/Explore 모드 전환
- **수정 파일:** `frontend/app/feed/page.tsx`
- **작업 내용:**
  - [x] `page_size=5` 요청 (기존 1 → 5, 다양성 확보용)
  - [x] `selectDiverseTop3()` 축 기반 선발 알고리즘 구현
    - Top1: 총점 1위 (종합 추천)
    - Top2: Top1과 다른 1순위 축 중 최고
    - Top3: Top1,2와 다른 축 중 최고
    - fallback: 축 동일 시 순차 선택
  - [x] `expandLevel` 상태: 0=Decision, 1=Explore(Top3)
  - [x] "비슷한 선택 보기" 보조 CTA (코디 2개 이상일 때만 표시)
  - [x] Explore Mode: compact 카드 Top2~3 표시, 축 라벨 강조
  - [x] compact 카드 탭 → 해당 코디를 decision으로 교체 → Decision Mode 복귀
  - [x] handleDecide / completeSurvey 구조 **변경 없음**
- **완료 기준:** ✅ 모두 충족
- **의존:** 없음

**Task 3.2v3 — OutfitCard compact variant + 라벨** ✅ `2026-03-31`
- **목적:** compact 카드 UI + 축 라벨 표시 + 선택 시 Decision Mode 복귀
- **수정 파일:** `frontend/components/OutfitCard.tsx`
- **작업 내용:**
  - [x] `variant` prop: `"full"` (기존 3:4) | `"compact"` (가로 썸네일 80x100 + 텍스트)
  - [x] `label` prop: 축 라벨 필 뱃지 (Marsala bg, "컬러 매칭형" 등)
  - [x] `onTap` prop: compact 카드 탭 시 호출
  - [x] compact에서 swipe/heart 비활성화 (단순 탭만)
  - [x] full variant에도 label 표시 가능 (Explore 진입 시 "1위 추천")
  - [x] DESIGN.md 준수: Surface bg(#F0EDE8), rounded-lg(8px), spacing 8px 기반
- **완료 기준:** ✅ 모두 충족
- **의존:** Task 3.1v3

### 🅑 측정 확장

**Task 3.3v3 — 측정 필드 확장** ✅ `2026-03-31`
- **목적:** Explore Mode 행동 데이터 수집
- **수정 파일:** `frontend/lib/api.ts`, `frontend/app/feed/page.tsx`
- **작업 내용:**
  - [x] `MetricsPayload`에 3개 필드 추가: `expanded`, `expand_level`, `selected_rank`
  - [x] `completeSurvey`에서 새 필드 포함하여 `postMetrics` 호출
  - [x] CSV export 컬럼 8개: `timestamp,ttd_ms,trust_score,confidence,cta_clicked,expanded,expand_level,selected_rank`
  - [x] Debug Panel에서 EXP/DEC, L0/L1, R1~3 표시
- **완료 기준:** ✅ 모두 충족
- **의존:** 없음

### W3-v3 완료 기준 ✅
- [x] Decision Mode에서 "비슷한 선택 보기" 버튼 동작 (Task 3.1v3)
- [x] Explore Mode에서 축 기반 Top3 카드 표시 + 선택 복귀 (Task 3.2v3)
- [x] 측정 데이터에 expanded/expand_level/selected_rank 포함 (Task 3.3v3)

---

## W4-v3: 통합 테스트 (4/14~4/18)

**Task 4.1v3 — 전체 흐름 통합 테스트**
- **목적:** Decision Mode + Explore Mode 전체 E2E 검증
- **수정 파일:** 테스트 파일
- **작업 내용:**
  - [ ] **시나리오 1: Decision Mode 즉시 결정**
    - 피드 진입 → Top1 확인 → "이걸로 결정" → 설문 → 이동
    - 측정: `expanded=false, expand_level=0, selected_rank=1`
  - [ ] **시나리오 2: Explore Mode → Top1 유지**
    - "비슷한 선택 보기" → Top3 확인 → Top1 탭 → 결정
    - 측정: `expanded=true, expand_level=1, selected_rank=1`
  - [ ] **시나리오 3: Explore Mode → Top2 선택**
    - "비슷한 선택 보기" → Top3 확인 → Top2 compact 카드 탭 → Decision Mode 복귀 → 결정
    - 측정: `expanded=true, expand_level=1, selected_rank=2`
  - [ ] **시나리오 4: Top5 확장**
    - "비슷한 선택 보기" → "더 보기" → Top5 → Top4 선택 → 결정
    - 측정: `expanded=true, expand_level=2, selected_rank=4`
  - [ ] **시나리오 5: TPO 변경 후 결정**
    - TPO 탭 변경 → Top1 새로 로드 → expandLevel 리셋 확인
  - [ ] **Edge Case:**
    - 코디 3개 미만일 때 Explore Mode (Top2만 표시)
    - 코디 1개일 때 "비슷한 선택 보기" 숨김
    - 설문 스킵 + Explore Mode 측정 동시 확인
  - [ ] **백엔드 단위 테스트:**
    - feed API page_size=3 응답 정상
    - feed API page_size=5 응답 정상
    - reason_generator: 서로 다른 outfit → 서로 다른 evidence 확인
- **완료 기준:**
  - 5개 시나리오 수동 테스트 통과
  - Edge case 통과
  - 백엔드 pytest 전체 통과
- **의존:** W3-v3 전체 완료

---

## W5-v3: QA + 배포 + 데모 (4/21~4/25)

**Task 5.1v3 — 반응형 QA**
- **수정 파일:** 프론트엔드 전반
- **작업 내용:**
  - [ ] 모바일 (375px): Decision Mode + Explore Mode 전체 확인
  - [ ] compact 카드가 375px에서 깨지지 않는지 확인
  - [ ] "이걸로 결정" CTA 터치 타겟 44px 이상
  - [ ] 설문 바텀시트 모바일 동작
  - [ ] 태블릿 (768px): 레이아웃 확인
- **완료 기준:**
  - 375px, 768px에서 두 모드 모두 정상
- **의존:** Task 4.1v3

**Task 5.3v3 — 성능 최적화**
- **작업 내용:**
  - [ ] Feed API 응답 시간 측정 (page_size=3 기준, 목표 800ms 이내)
  - [ ] Explore Mode 전환 시 추가 로딩 시간 체감 확인
  - [ ] 이미지 lazy loading 확인 (compact 카드 포함)
- **완료 기준:**
  - Feed API page_size=3: 800ms 이내
  - Explore Mode 전환 체감 1초 이내
- **의존:** Task 5.1v3

**Task 5.4v3 — 버그 수정**
- **작업 내용:**
  - [ ] W3~W4에서 발견된 버그 수정
  - [ ] 크로스 브라우저 테스트 (Chrome, Safari)
- **완료 기준:**
  - Decision/Explore 흐름에 blocking 버그 없음
- **의존:** Task 4.1v3

**Task 5.5v3 — 프로덕션 배포**
- **작업 내용:**
  - [ ] 프론트엔드 프로덕션 빌드 + Vercel 배포
  - [ ] 백엔드 프로덕션 설정 + Railway 배포
  - [ ] 프로덕션 URL 접속 확인
- **완료 기준:**
  - 프로덕션 URL에서 Decision + Explore 모두 동작
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
- **완료 기준:**
  - 데모 시나리오 3개 동작 확인
  - KPI 비교 수치 제시 가능
- **의존:** Task 5.5v3

### W5-v3 완료 기준
- [ ] 프로덕션 URL 접속 가능 (Task 5.5v3)
- [ ] Decision + Explore 흐름 버그 없음 (Task 5.4v3)
- [ ] 데모 준비 완료 (Task 5.6v3)
- [ ] Decision Mode TTD < 15초 (Task 5.3v3)

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

## Fallback 순서 (W3-v3 금요일 판단)

밀릴 경우 아래 순서로 2차 미룸:
1. Top5 확장 (expandLevel=2) — Top3까지만 유지
2. compact 카드 차별화 UI — 리스트 형태로 단순화
3. 프로필/마이페이지 — 홈 화면만으로 동작
4. 반응형 QA 태블릿 — 모바일만 확인

**절대 미루지 않는 것:**
Decision Mode (Top1 + 설득) → "비슷한 선택 보기" → Top3 Explore → 측정 확장
