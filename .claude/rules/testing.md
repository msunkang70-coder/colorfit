---
paths:
  - "backend/tests/**/*.py"
  - "frontend/**/*.test.ts"
  - "frontend/**/*.test.tsx"
---

# Testing Rules

## 원칙
- 핵심 서비스(scoring, style_filter, feed_builder) 100% 커버리지 목표
- 테스트는 가상환경 하에서 진행
- `expect(x).toBeDefined()` 같은 존재 확인 테스트 금지. 실제 동작을 테스트할 것

## 백엔드 (pytest)
- 파일명: `test_{모듈명}.py`
- 픽스처로 테스트 데이터 관리
- scoring 함수는 순수 함수이므로 mock 없이 직접 테스트
- DB 테스트는 테스트용 SQLite 사용

## 프론트엔드 (vitest + @testing-library/react)
- 파일명: `{컴포넌트명}.test.tsx`
- 사용자 관점 테스트 (DOM 구조가 아닌 화면에 보이는 것 테스트)
- API 호출은 MSW로 mock

## Edge Case 필수
- H7 톤 필터율 30% 상한 검증
- 예산 50%+ 초과 Hard Filter 확인
- 코디 0개 결과 시 empty state
- 동일 톤 3개 제한 (다양성)
- 5축 스코어 각 경계값 (0점, 100점, 75점 분기)
