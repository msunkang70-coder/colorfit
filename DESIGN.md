# Design System — ColorFit

<!--
  ┌─────────────────────────────────────────────────────┐
  │  이 파일의 구조 (위에서 아래로 읽으면 됩니다)           │
  │                                                     │
  │  1. Product Context      — 서비스 정의               │
  │  2. Aesthetic Direction   — 디자인 방향성              │
  │  3. Typography            — 서체 규칙                 │
  │  4. Color                 — 컬러 시스템 (라이트 기준)   │
  │     └ Score Axis / Semantic / Dark Mode 토큰          │
  │  5. Spacing               — 여백 (8px 베이스)         │
  │  6. Layout                — 레이아웃 + border-radius   │
  │  7. Motion                — 애니메이션 규칙            │
  │  8. Components            — 버튼/태그/카드/인풋        │
  │  9. Card Variants (v3)    — Full/Compact 카드         │
  │ 10. ★ Dark Glassmorphism Theme (v4) — 현재 테마 전부  │
  │     ├ 컬러 토큰 (다크 모드 실제 값)                    │
  │     ├ 글래스모피즘 컴포넌트 (glass-card/cta/chip)      │
  │     ├ 배경 이미지 시스템 (7화면 × 남녀)                │
  │     ├ 레이아웃 모드 (프로덕션 vs 데모)                 │
  │     ├ 화면별 DOM 구조                                 │
  │     └ 설문 바텀시트 (Quick Survey)                    │
  │ 11. Decisions Log         — 디자인 결정 이력           │
  │                                                     │
  │  ★ 현재 앱에 적용된 디자인은 10번 섹션이 핵심입니다     │
  │  구현 파일: frontend/app/globals.css                   │
  │  배경 이미지: frontend/public/images/style/            │
  └─────────────────────────────────────────────────────┘
-->

<!-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ -->
<!-- 1. 서비스 정의 — 이 서비스가 뭔지, 누구를 위한 건지     -->
<!-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ -->
## Product Context
- **What this is:** AI 퍼스널컬러 기반 패션 의사결정 엔진. 진단 결과를 실제 쇼핑에 연결한다.
- **Who it's for:** 20대 중후반 여성, 퍼스널컬러 진단 후 쇼핑에 활용 못하는 사람
- **Space/industry:** 퍼스널컬러 × 패션 커머스. 경쟁자: mycolor.kr, Dressika, 잼페이스(뷰티 앱), Fits, Indyx(스타일링 앱)
- **Project type:** 모바일 웹 (반응형, 모바일 퍼스트)

<!-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ -->
<!-- 2. 디자인 방향성 — 어떤 느낌을 추구하는지               -->
<!--    경쟁사 대비 차별화 포인트: "뷰티 앱"이 아닌 "패션 매거진" -->
<!-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ -->
## Aesthetic Direction
- **Direction:** Editorial/Magazine
- **Decoration level:** Intentional (여백이 고급스러움을 만든다. 장식은 최소한)
- **Mood:** 패션 매거진 표지를 넘기는 느낌. 이미지가 주인공, 텍스트는 보조. 성숙하고 신뢰감 있으면서 따뜻한 톤. COS, Vogue Korea 문법.
- **Differentiation:** 모든 경쟁 퍼스널컬러 앱이 파스텔 핑크/퍼플 "뷰티 앱"으로 보이는데, ColorFit만 "패션 매거진"으로 보인다. 이것이 핵심 차별화.
- **Reference:** COS(여백+세리프+뉴트럴), SSENSE(풀블리드+미니멀 타이포), Farfetch(카드+가격 표시), Pinterest(저장 인터랙션)

<!-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ -->
<!-- 3. 서체 — 헤드라인(Nanum Myeongjo) + 본문(Pretendard) -->
<!--    h1~h3, body, caption, micro 사이즈 스케일 정의      -->
<!-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ -->
## Typography
- **Display/Hero:** Nanum Myeongjo 700/800 — 한국 에디토리얼의 클래식. Vogue Korea, W Korea가 실제로 쓰는 서체. 얇고 우아한 획이 패션 매거진 무드를 만든다.
- **Body:** Pretendard Variable 400/500/600 — 한글 가독성 최적화. 다양한 웨이트로 위계 표현. 검증된 본문체.
- **UI/Labels:** Pretendard Variable 500/600
- **Data/Tables:** Pretendard Variable (font-variant-numeric: tabular-nums)
- **Code:** JetBrains Mono (내부 개발용만)
- **Loading:** Google Fonts CDN (`family=Nanum+Myeongjo:wght@400;700;800`)
- **Scale:**
  - h1: 36px / Nanum Myeongjo 700 / line-height 1.15
  - h2: 24px / Nanum Myeongjo 700 / line-height 1.25
  - h3: 18px / Nanum Myeongjo 700 / line-height 1.3
  - body: 16px / Pretendard 400 / line-height 1.6
  - caption: 13px / Pretendard 400 / line-height 1.5
  - micro: 11px / Pretendard 400 / line-height 1.4

<!-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ -->
<!-- 4. 컬러 시스템 — 라이트 모드 기준 (원본)                -->
<!--    Accent: Marsala #964F4C (핵심 브랜드 컬러)          -->
<!--    다크 모드 실제 값은 아래 "Dark Glassmorphism" 섹션   -->
<!-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ -->
## Color
- **Approach:** Restrained. UI는 뉴트럴, 색상은 코디 이미지에 양보한다.
- **Primary:** #222222 (Charcoal Black) — 텍스트, 헤더, Primary 버튼
- **Background:** #F8F6F3 (Warm Off-White) — 페이지 배경
- **Surface:** #F0EDE8 (Warm Beige Card) — 카드 배경, 섹션 구분
- **Accent (CTA):** #964F4C (Marsala) — CTA 버튼, 강조 텍스트, 활성 탭. 와인 같은 적갈색으로 파스텔 핑크 경쟁자 대비 강력한 차별화.
- **Sub Accent:** #D4A5A5 (Soft Pink) — 태그, 배지, 보조 강조
- **Warm Neutral:** #F5DEB3 (Wheat) — 배경 구분, Sub Surface 보조
- **Border:** #E5E1DA (Wheat Beige) — 구분선, 카드 테두리
- **Text Secondary:** #8C8578 (Warm Gray) — 보조 텍스트
- **Text Tertiary:** #B5AFA6 (Sand) — 캡션, 비활성 텍스트

### Score Axis Colors
모든 축이 웜/뉴트럴 톤으로 통일. 동시 배치 시 시각 조화 확보.

| Axis | Name | HEX | Usage |
|------|------|-----|-------|
| tpo | Marsala | #964F4C | TPO 최적형 |
| fit | Ocean Blue | #4F97A3 | 핏 추천형 |
| color | Honey Gold | #A07830 | 컬러 매칭형 |
| style | Grape Compote | #6B5B8A | 스타일 통일형 |

Score bar track (미충전): #E5E1DA (Border)

### Semantic Colors (Warm-toned)
표준 시맨틱 컬러 대신 웜 팔레트와 조화하는 톤 사용.

| State | Background | Text | Border |
|-------|-----------|------|--------|
| Success | #F0EDE8 | #6B7F5E | #D4DCCC |
| Warning | #F5F0E8 | #A07830 | #E5D9C0 |
| Error | #F5EDEC | #964F4C | #E0CBC9 |
| Info | #EDF3F4 | #4F97A3 | #C8DDE0 |

### Dark Mode
웜 언더톤 유지. 쿨그레이 배경 사용 안 함. 순수 블랙이 아닌 #1A1714.

| Token | Light | Dark |
|-------|-------|------|
| bg-primary | #F8F6F3 | #1A1714 |
| bg-secondary | #F0EDE8 | #242018 |
| text-primary | #222222 | #F0EDE8 |
| brand-accent | #964F4C | #C4726F |
| score-tpo | #964F4C | #C4726F |
| score-fit | #4F97A3 | #6BADB9 |
| score-color | #A07830 | #C49540 |
| score-style | #6B5B8A | #8971A6 |

<!-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ -->
<!-- 5. 여백 — 8px 베이스, 2xs~3xl 스케일                   -->
<!-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ -->
## Spacing
- **Base unit:** 8px
- **Density:** Comfortable
- **Scale:** 2xs(2) xs(4) sm(8) md(16) lg(24) xl(32) 2xl(48) 3xl(64)

<!-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ -->
<!-- 6. 레이아웃 — 그리드, max-width, border-radius         -->
<!-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ -->
## Layout
- **Approach:** Hybrid. 피드는 카드 그리드, 온보딩은 풀스크린 에디토리얼.
- **Grid:** 모바일 1열, 태블릿 2열
- **Max content width:** 768px (모바일 웹 최적화)
- **Border radius:**
  - sm: 4px (태그, 배지)
  - md: 8px (카드, 입력)
  - lg: 12px (모달, 바텀시트)
  - xl: 16px (온보딩 카드)
  - full: 9999px (필, 아바타)

<!-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ -->
<!-- 7. 모션 — Framer Motion spring 기반, 장식 애니메이션 금지 -->
<!-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ -->
## Motion
- **Approach:** Intentional. 의미 있는 모션만. 장식 아님.
- **Library:** Framer Motion 11 (spring 물리 기반)
- **Easing:** enter(ease-out) exit(ease-in) move(ease-in-out)
- **Duration:** micro(50-100ms) short(150-250ms) medium(250-400ms) long(400-700ms)
- **Key interactions:**
  - 카드 등장: fadeInUp (y:30→0, opacity:0→1), 0.4s, stagger 0.1s
  - 저장 하트: scale 0.8→1.2→1.0, 0.3s + Marsala 색 전환
  - 피드→상세: Shared Element Transition (layoutId)
  - 스코어 바: width 0%→실제값, ease-out 0.8s, stagger 0.15s
  - 바텀시트: y:100%→0, spring(stiffness:300, damping:30)
- **Rule:** `prefers-reduced-motion` 존중. `transition: all` 금지. transform/opacity만 애니메이션.

<!-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ -->
<!-- 8. 공통 컴포넌트 — 버튼/태그/카드/인풋 기본 스타일       -->
<!-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ -->
## Components
- **Buttons:** Primary(Marsala bg, white text), Secondary(Marsala outline), Ghost(border only)
- **Pills/Tags:** Active(Marsala bg), Inactive(Surface bg + border), Score(Surface bg)
- **Cards:** Surface bg, border, rounded-lg(8px)
- **Inputs:** bg-primary, border, rounded-md, focus시 border → Marsala
- **Alerts:** 웜 톤 시맨틱 (위 Semantic Colors 참조)

<!-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ -->
<!-- 9. 카드 변형 — Full(기본) / Compact(Explore) / 축 뱃지  -->
<!-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ -->
## Card Variants (v3)
- **Full Card:** 기본 코디 카드. 3:4 이미지 + core(Nanum Myeongjo 16px) + price + evidence + risk_guard. padding 0 20px.
- **Compact Card:** Explore Mode 축소 카드. Surface bg(#F0EDE8), rounded-lg(8px), padding 12px. 가로 배치: 썸네일(80x100, rounded-md) + 텍스트(core 14px + price 14px + evidence 12px 1줄). 탭 시 해당 코디 선택.
- **Axis Label Badge:** 축 라벨 필 뱃지. Marsala bg(#964F4C), white text, rounded-full, fontSize 10~11px, padding 2-3px 8-10px. Full/Compact 모두 사용.

<!-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ -->
<!-- ★ 10. 다크 글래스모피즘 테마 — 현재 앱에 적용된 핵심 섹션 -->
<!--    구현 파일: frontend/app/globals.css                 -->
<!--    배경 이미지: frontend/public/images/style/           -->
<!--    레이아웃: frontend/app/layout.tsx                    -->
<!-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ -->
## Dark Glassmorphism Theme (v4, 2026-04-10~)

현재 앱의 기본 테마. iOS 다크 모드 + 글래스모피즘 기반.

### 핵심 원칙
- 배경: 풀스크린 룩북 이미지 + 다크 그래디언트 오버레이
- UI 요소: 반투명 유리(blur) 카드 위에 배치
- 순수 블랙 사용 금지 → `#1A1714` (웜 차콜)
- 순수 흰색 사용 금지 → `rgba(255,255,255,0.XX)` 투명도로 위계 표현

### 컬러 토큰 (다크 모드)
| Token | Value | Usage |
|-------|-------|-------|
| bg-base | `#1A1714` | 페이지 배경 |
| bg-card | `rgba(255,255,255,0.08)` | 글래스 카드 |
| bg-card-active | `rgba(150,79,76,0.15)` | 선택된 카드 |
| text-primary | `rgba(240,237,232,0.9)` | 주요 텍스트 |
| text-secondary | `rgba(255,255,255,0.5)` | 보조 텍스트 |
| text-tertiary | `rgba(255,255,255,0.25)` | 캡션/비활성 |
| border | `rgba(255,255,255,0.1)` | 카드/구분선 |
| accent | `#964F4C` / `#C4726F` | CTA/강조 |
| success | `rgba(107,127,94,0.9)` | risk_guard 안전 |
| warning | `rgba(160,120,48,0.9)` | 주의 |

### 글래스모피즘 컴포넌트
구현: `frontend/app/globals.css`

| 컴포넌트 | 배경 | blur | border | 용도 |
|---------|------|------|--------|------|
| `.glass-card` | `rgba(255,255,255,0.08)` | 12px | `rgba(255,255,255,0.1)` | 온보딩 선택 카드 |
| `.glass-card.active` | `rgba(150,79,76,0.15)` | 12px | `rgba(150,79,76,0.5)` | 선택된 상태 |
| `.glass-cta` | `linear-gradient(#7A3E3C → #964F4C → #B5605D)` | — | — | CTA 버튼 |
| `.glass-chip` | `rgba(255,255,255,0.06)` | — | `rgba(255,255,255,0.1)` | TPO/무드 칩 |
| `.glass-chip.on` | `rgba(150,79,76,0.25)` | — | `#964F4C` | 선택된 칩 |
| 설문 바텀시트 | `rgba(30,27,24,0.95)` | 20px | `rgba(255,255,255,0.08)` | Quick Survey |

### 배경 이미지 시스템
구현: `frontend/app/globals.css`, 이미지 위치: `frontend/public/images/style/`

**구조:** 풀스크린 이미지 → 다크 그래디언트 오버레이 → 콘텐츠

| 화면 | 여성 이미지 | 남성 이미지 | CSS 클래스 |
|------|-----------|-----------|-----------|
| Welcome | `style_1.jpg` | `style_1.jpg` | `.welcome-bg` |
| Step1 성별 | `style_1.jpg` | `style_1.jpg` | `.ob-bg-step1` |
| Step2 톤 | `style_8.jpg` | `male_8.jpg` | `.ob-bg-step2-f/m` |
| Step3 TPO+무드 | `style_5.jpg` | `male_5.jpg` | `.ob-bg-step3-f/m` |
| Step4 예산 | `style_12.jpg` | `male_4.jpg` | `.ob-bg-step4-f/m` |
| Step5 취향 | `style_4.jpg` | `male_1.jpg` | `.ob-bg-step5-f/m` |
| Feed | `style_1.jpg` | `male_1.jpg` | `.feed-bg-f/m` |

**오버레이 그래디언트:**
- 온보딩: `rgba(20,18,16, 0.1→0.45→0.82→0.96)` — 하단으로 갈수록 어두워짐
- Welcome: `rgba(20,18,16, 0.05→0.35→0.8→0.97)` — 콘텐츠 영역 가독성 확보
- Feed: `rgba(20,18,16, 0.65)` 균일 + 이미지 `brightness(0.3) saturate(0.3) blur(6px)`

**성별 분기:** Step1에서 성별 선택 시 Step2~5 + Feed 배경이 자동 전환

### 레이아웃 모드
구현: `frontend/app/layout.tsx`

| 모드 | 조건 | 레이아웃 |
|------|------|---------|
| **프로덕션** | `NEXT_PUBLIC_DEMO_MODE` 미설정 | 풀스크린, max-width 480px, DemoPanel 없음 |
| **데모** | `NEXT_PUBLIC_DEMO_MODE=true` | iPhone 15 Pro 프레임(393×852) + 우측 DemoPanel |

**프로덕션 (`.prod-wrapper`):** `max-width: 480px; margin: 0 auto;`
**데모 (`.app-frame`):** `width: 393px; min-height: 852px; border-radius: 40px; border: 6px solid #3A3530;`

### 화면별 구조
| 화면 | 파일 | 배경 구조 |
|------|------|----------|
| Welcome | `frontend/app/page.tsx` | `.welcome-page > .welcome-bg + .welcome-overlay + .welcome-content` |
| 온보딩 | `frontend/app/onboarding/step*/page.tsx` | `.ob-page > .ob-bg + .ob-overlay + .ob-content` |
| Feed | `frontend/app/feed/page.tsx` | `.feed-page > .feed-bg + .feed-overlay + 콘텐츠` |

### 설문 바텀시트 (Quick Survey)
구현: `frontend/app/feed/page.tsx`

- 다크 반투명 배경: `rgba(30,27,24,0.95)` + `blur(20px)`
- 드래그 핸들 + "Quick Survey" 태그
- Q1 신뢰도: 1~5 버튼 (글래스 카드 안) + 양끝 라벨
- Q2 구매 확신: 👍/👎 이모지 + 시맨틱 컬러 (초록=네, 노랑=아니요)
- 제출 CTA: 입력 시 Marsala 그래디언트 활성화 + 글로우 섀도우

<!-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ -->
<!-- 11. 디자인 결정 이력 — 왜 이렇게 결정했는지 기록         -->
<!--     날짜순. 새로운 결정은 맨 아래에 추가                  -->
<!-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ -->
## Decisions Log
| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-28 | Nanum Myeongjo로 헤드라인 서체 변경 | Noto Serif KR이 "애매"하다는 피드백. Nanum Myeongjo는 한국 패션 매거진의 실제 서체로 에디토리얼 무드를 강화한다 |
| 2026-03-31 | Compact Card variant 추가 | Explore Mode Top2~3 표시용. Surface bg + 가로 배치로 Full Card 대비 시각적 위계 구분 |
| 2026-03-31 | Axis Label Badge 정의 | Top3 차별화 인지용. Marsala pill로 디자인 시스템 내 Pills/Tags Active 스타일 재사용 |
| 2026-03-28 | Alert 색상 웜 톤으로 교체 | 표준 시맨틱 컬러(초록/노랑/빨강/파랑)가 웜 팔레트와 동떨어진다는 피드백. Marsala/Ocean Blue 계열로 통일 |
| 2026-03-28 | Marsala #964F4C를 Accent으로 확정 | 모든 경쟁 퍼스널컬러 앱이 핑크/퍼플을 쓰는 가운데, 와인 적갈색은 즉각적인 차별화. REFERENCE X Vol.1 기반 |
| 2026-03-28 | Initial design system created | /design-consultation 리서치(mycolor.kr, Fits, SSENSE/COS 레퍼런스) + 기획서 v1.3 디자인 시스템 검증 기반 |
| 2026-04-10 | 다크 글래스모피즘 테마 전환 | 라이트 모드 → 다크 모드. 이유: 패션 매거진 무드 강화, 이미지 중심 UI에서 다크 배경이 상품 이미지를 더 돋보이게 함 |
| 2026-04-10 | 배경 이미지 + 오버레이 구조 도입 | 각 화면별 풀스크린 룩북 이미지 + 다크 그래디언트 오버레이. 성별 선택 시 남/여 이미지 자동 전환 |
| 2026-04-10 | 글래스모피즘 컴포넌트 체계화 | glass-card, glass-cta, glass-chip 3종. backdrop-filter: blur 기반. iOS 디자인 랭귀지 참조 |
| 2026-04-11 | 프로덕션/데모 모드 분리 | NEXT_PUBLIC_DEMO_MODE 환경변수로 분기. 프로덕션은 풀스크린, 데모는 iPhone 프레임+DemoPanel |
| 2026-04-11 | 설문 UI 다크 글래스모피즘 리디자인 | 라이트 바텀시트 → 다크 blur 20px. Quick Survey 태그 + 이모지 + 시맨틱 컬러 |
| 2026-04-12 | 상품 링크 "유사 상품 찾기"로 변경 | 정적 데이터 MVP 특성상 상품 삭제/품절 대응. 직접 링크 → 네이버 쇼핑 검색 |
