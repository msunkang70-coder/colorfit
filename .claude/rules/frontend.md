---
paths:
  - "frontend/**/*.tsx"
  - "frontend/**/*.ts"
  - "frontend/**/*.css"
---

# Frontend Rules (Next.js 15 + React 19)

## 코딩 규칙
- 함수형 컴포넌트만 사용. class 컴포넌트 금지
- 컴포넌트명: PascalCase, 변수/함수명: camelCase
- 들여쓰기: 2 spaces
- Props는 interface로 정의 (type 아닌 interface)

## 디자인 시스템
- 반드시 `DESIGN.md`를 읽고 UI 구현할 것
- 서체: Nanum Myeongjo (헤드라인), Pretendard Variable (본문)
- 액센트: Marsala #964F4C. 다른 액센트 컬러 임의 사용 금지
- 배경: #F8F6F3 (라이트), #1A1714 (다크). 순수 흰색/검정 사용 금지
- 시맨틱 컬러는 웜 톤 사용 (표준 초록/빨강/파랑 아님). DESIGN.md 참조
- border-radius: sm(4px), md(8px), lg(12px), xl(16px), full(9999px)
- spacing: 8px 베이스 (2, 4, 8, 16, 24, 32, 48, 64)

## 모션
- Framer Motion spring 물리 사용. CSS transition 대신
- 의미 있는 모션만. 장식 애니메이션 금지
- `prefers-reduced-motion` 존중
- `transition: all` 금지. 속성 명시

## 상태 관리
- 로딩: 스켈레톤 UI (펄스 애니메이션)
- empty state: 일러스트 + 안내 텍스트 + CTA 버튼
- error state: 구체적 메시지 + 재시도 버튼
- 모든 화면에 loading/empty/error/success 4가지 상태 구현

## 이미지
- aspect-ratio 3:4 (코디 이미지)
- loading="lazy" 필수
- width/height 명시

## Task 업데이트
- 프론트엔드 Task 완료 시 TASK.md 즉시 업데이트
