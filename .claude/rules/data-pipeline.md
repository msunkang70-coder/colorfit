---
paths:
  - "backend/scripts/**/*.py"
  - "backend/data/**/*"
---

# Data Pipeline Rules

## 수집 (scripts/curate_by_tone.py)
- 네이버 쇼핑 API 25,000회/일 제한 준수
- 4톤 병렬 수집 x 3라운드 = 12톤 커버
- API 응답은 raw JSON으로 먼저 저장, 전처리는 별도 단계
- Rate limit 에러 시 exponential backoff (1s → 2s → 4s)

## 전처리 (scripts/rebuild_from_tones.py)
- HTML 태그 제거 (title의 <b> 등)
- 이미지 색상 추출: PIL + K-means (상위 3개 클러스터)
- 12톤 매핑: RGB 유클리드 거리 (최소 거리 톤 선택)
- 하이브리드 분류: 키워드 먼저(~70%) → LLM 캐시(~27%) → 실시간 LLM(~3%)
- LLM 분류 결과는 JSON 캐시에 저장 (재실행 시 API 호출 절약)

## 코디 생성
- 레시피 기반 (랜덤 조합 금지)
- TPO x 무드 x 성별별 레시피 JSON 정의
- 금지 카테고리 검증 필수
- 포멀도 편차 2 이내
- 중복 조합 검증

## 품질 평가 (scripts/evaluate_outfits.py)
- Gemini Flash 배치 평가
- 3점 미만 제거
- 결과를 outfits.llm_quality_score에 저장

## 데이터 파일 규칙
- data/palettes/: 12톤 팔레트 JSON (수정 시 주의)
- data/style_compat.json: 227개 카테고리 궁합 매트릭스
- data/brand_whitelist.json: 브랜드 화이트리스트
- 이 파일들은 소스 코드로 취급. 변경 시 커밋 메시지에 명시
