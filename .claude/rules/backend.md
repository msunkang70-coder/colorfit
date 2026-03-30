---
paths:
  - "backend/**/*.py"
---

# Backend Rules (FastAPI + Python 3.13)

## 코딩 규칙
- snake_case (함수, 변수, 파일명)
- 들여쓰기: 4 spaces
- type hint 필수 (함수 파라미터 + 반환값)
- Pydantic v2 모델로 요청/응답 검증

## 아키텍처
- routers/: API 엔드포인트 (라우팅만, 비즈니스 로직 넣지 않기)
- services/: 비즈니스 로직 (순수 함수 우선)
- models/: SQLAlchemy ORM 모델
- schemas/: Pydantic 스키마 (요청/응답 DTO)

## 추천 엔진 규칙
- scoring.py의 5축 함수는 순수 함수로 구현 (DB 의존 없음)
- Hard Filter(탈락)와 Soft Score(순위)를 절대 섞지 않는다
- H7 톤 필터: P1 우선 원칙. 필터율 30% 넘으면 호환 톤 집합 확장
- 스코어는 프리컴퓨팅 (outfits.scores JSONB). 런타임에는 개인화 보정만

## DB
- SQLAlchemy 2.0 스타일 (select() 함수 사용, session.query() 아님)
- 페이지네이션: 커서 기반 (OFFSET 아님)
- 인덱스: tone_id, designed_tpo, gender에 반드시 생성

## 에러 처리
- HTTPException으로 클라이언트 에러 반환
- 500 에러는 로깅 후 일반 메시지 반환 (내부 정보 노출 금지)
- Gemini API 호출 실패 시 graceful fallback (스코어링은 규칙 기반으로)

## 환경변수
- .env 파일 절대 커밋하지 않기
- .env.example에 키 이름만 기록
- NAVER_CLIENT_ID, NAVER_CLIENT_SECRET, GEMINI_API_KEY, DATABASE_URL

## Task 업데이트
- 백엔드 Task 완료 시 TASK.md 즉시 업데이트
