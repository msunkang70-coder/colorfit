# Design System — ColorFit

## Product Context
- **What this is:** AI 퍼스널컬러 기반 패션 의사결정 엔진. 진단 결과를 실제 쇼핑에 연결한다.
- **Who it's for:** 20대 중후반 여성, 퍼스널컬러 진단 후 쇼핑에 활용 못하는 사람
- **Space/industry:** 퍼스널컬러 × 패션 커머스. 경쟁자: mycolor.kr, Dressika, 잼페이스(뷰티 앱), Fits, Indyx(스타일링 앱)
- **Project type:** 모바일 웹 (반응형, 모바일 퍼스트)

## Aesthetic Direction
- **Direction:** Editorial/Magazine
- **Decoration level:** Intentional (여백이 고급스러움을 만든다. 장식은 최소한)
- **Mood:** 패션 매거진 표지를 넘기는 느낌. 이미지가 주인공, 텍스트는 보조. 성숙하고 신뢰감 있으면서 따뜻한 톤. COS, Vogue Korea 문법.
- **Differentiation:** 모든 경쟁 퍼스널컬러 앱이 파스텔 핑크/퍼플 "뷰티 앱"으로 보이는데, ColorFit만 "패션 매거진"으로 보인다. 이것이 핵심 차별화.
- **Reference:** COS(여백+세리프+뉴트럴), SSENSE(풀블리드+미니멀 타이포), Farfetch(카드+가격 표시), Pinterest(저장 인터랙션)

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
| PCF | Marsala | #964F4C | 퍼스널컬러 적합도 |
| OF | Ocean Blue | #4F97A3 | TPO 적합도 |
| CH | Honey Gold | #DDB67D | 색상 조화 |
| PE | Autumn Blaze | #D1933F | 가격 효율 |
| SF | Grape Compote | #6B5876 | 스타일 핏 |

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
| score-pcf | #964F4C | #C4726F |
| score-of | #4F97A3 | #6BADB9 |
| score-ch | #DDB67D | #E8C693 |
| score-pe | #D1933F | #DBA84F |
| score-sf | #6B5876 | #896E96 |

## Spacing
- **Base unit:** 8px
- **Density:** Comfortable
- **Scale:** 2xs(2) xs(4) sm(8) md(16) lg(24) xl(32) 2xl(48) 3xl(64)

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

## Components
- **Buttons:** Primary(Marsala bg, white text), Secondary(Marsala outline), Ghost(border only)
- **Pills/Tags:** Active(Marsala bg), Inactive(Surface bg + border), Score(Surface bg)
- **Cards:** Surface bg, border, rounded-lg(8px)
- **Inputs:** bg-primary, border, rounded-md, focus시 border → Marsala
- **Alerts:** 웜 톤 시맨틱 (위 Semantic Colors 참조)

## Decisions Log
| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-28 | Nanum Myeongjo로 헤드라인 서체 변경 | Noto Serif KR이 "애매"하다는 피드백. Nanum Myeongjo는 한국 패션 매거진의 실제 서체로 에디토리얼 무드를 강화한다 |
| 2026-03-28 | Alert 색상 웜 톤으로 교체 | 표준 시맨틱 컬러(초록/노랑/빨강/파랑)가 웜 팔레트와 동떨어진다는 피드백. Marsala/Ocean Blue 계열로 통일 |
| 2026-03-28 | Marsala #964F4C를 Accent으로 확정 | 모든 경쟁 퍼스널컬러 앱이 핑크/퍼플을 쓰는 가운데, 와인 적갈색은 즉각적인 차별화. REFERENCE X Vol.1 기반 |
| 2026-03-28 | Initial design system created | /design-consultation 리서치(mycolor.kr, Fits, SSENSE/COS 레퍼런스) + 기획서 v1.3 디자인 시스템 검증 기반 |
