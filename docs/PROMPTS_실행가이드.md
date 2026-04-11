# ColorFit 추천 시스템 개선 — Claude Code 실행 프롬프트

## 실행 순서 맵

```
Step 1 (데이터) → Step 2 (즉시 코드 수정) → Step 3 (구조 리팩토링) → Step 4 (검증)
     │                   │                        │                      │
  color_hex 채우기     CH가중치0              4단계 파이프라인          pytest 전체
  시즌 태그 추가       JSON 캐싱             Eligibility 분리          데이터 검증
  workout 보강         CORS 수정             Expert Rerank             E2E 시나리오
```

> 각 Step의 프롬프트를 Claude Code 터미널에 **그대로 복붙**하면 됩니다.
> Step 1 완료 후 Step 2, Step 2 완료 후 Step 3 순서로 진행하세요.

---

## Step 1. 데이터 보강 (최우선)

### Prompt 1-1. color_hex 추출 스크립트

```
backend/data/outfits_scored.json을 읽어서 모든 아이템의 color_hex가 비어있는 것을 확인해.

다음 스크립트를 만들어줘:
파일: backend/scripts/fill_color_hex.py

목적: 각 아이템의 image_url에서 대표 색상을 추출하여 color_hex 필드를 채운다.

로직:
1. outfits_scored.json 로드
2. 각 아이템의 image_url에서 이미지 다운로드 (requests, referrer 헤더 포함)
3. Pillow로 이미지를 32x32로 리사이즈
4. 중앙 영역(16x16)의 평균 RGB 계산
5. RGB → HEX 변환하여 color_hex에 저장
6. 결과를 outfits_scored.json에 덮어쓰기

주의사항:
- 네이버 쇼핑 이미지(shopping-phinf.pstatic.net)는 Referer 헤더 필요
- 이미지 다운로드 실패 시 color_hex = "#808080" (회색) fallback
- 진행률 표시 (tqdm)
- 배치 처리: 10개씩 처리 후 중간 저장
- 이미 color_hex가 있는 아이템은 스킵

pip install Pillow requests tqdm 먼저 설치해줘.
실행 후 결과 통계를 출력해줘 (성공/실패/스킵 건수).
```

### Prompt 1-2. 시즌 태그 자동 태깅

```
backend/data/outfits_scored.json에 시즌 태그(spring/summer/autumn/winter)가 0개인 문제를 해결해줘.

파일: backend/scripts/fill_season_tags.py

로직:
1. 각 코디의 아이템 카테고리와 상품명을 분석
2. 다음 규칙으로 시즌 태깅:
   - 패딩, 코트, 플리스, 기모 → winter
   - 니트, 가디건, 트렌치 → autumn, spring
   - 반팔, 린넨, 반바지, 샌들 → summer
   - 셔츠, 블라우스, 슬랙스 → spring, autumn (멀티시즌)
   - 맨투맨, 후드, 청바지 → spring, autumn, winter (3시즌)
   - 특정 시즌 키워드 없으면 → 4시즌 전체
3. tags 배열에 시즌 태그 추가 (기존 태그 유지)
4. outfits_scored.json 덮어쓰기

결과 통계:
- 시즌별 코디 수
- 멀티시즌 코디 수
- 태깅 불가 코디 수

실행해줘.
```

### Prompt 1-3. workout 코디 보강

```
현재 outfits_scored.json에서 workout TPO 코디가 8개뿐이야.
최소 50개 이상으로 보강해야 해.

파일: backend/scripts/generate_workout_outfits.py

방법:
1. 기존 outfits_scored.json에서 casual/weekend TPO 코디 중 활동적인 카테고리(맨투맨, 후드, 레깅스, 조거팬츠, 티셔츠, 반바지) 포함 코디를 찾아서
2. designed_tpo에 "workout"을 추가하는 방식으로 코디를 복제/변환
3. 총 workout 코디가 50개 이상이 되도록
4. 복제 시 outfit_id는 새로 생성 (기존 id + "_workout" suffix)
5. formality_avg를 2 이하로 조정 (운동은 캐주얼)

기존 8개는 유지하고 추가분만 append.
outfits_scored.json에 저장.
전후 TPO 분포 통계 출력.
```

---

## Step 2. 즉시 코드 수정 (P0)

### Prompt 2-1. CH 가중치 0 + 동적 가중치 조정

```
docs/SYSTEM_REDESIGN_v3.md를 읽어.

backend/app/services/feed_builder.py의 compute_soft_scores() 함수를 수정해줘.

변경 내용:
1. _adjust_weights_by_data_quality() 함수 신규 추가
   - outfits 샘플 10개의 color_hex를 검사
   - 전부 비어있으면 CH 가중치를 0으로 설정
   - 나머지 축(pcf, of, pe, sf) 가중치를 정규화하여 합이 1.0이 되도록 재분배
2. compute_soft_scores()에서 이 함수를 호출하여 effective_weights 사용
3. score_and_rerank()에서도 effective_weights를 한 번만 계산하여 재사용

기존 DEFAULT_WEIGHTS는 유지 (color_hex 보강 후 자동 복원되도록).
기존 테스트가 깨지지 않도록 주의.
수정 후 pytest 실행해줘.
```

### Prompt 2-2. JSON 로딩 캐싱

```
backend/app/routers/feed.py의 _load_outfits_from_json()을 수정해줘.

현재: 매 API 요청마다 outfits_scored.json (1,500개) 전체 파일 I/O
변경: 모듈 레벨 캐싱으로 첫 요청에만 로드

구현:
1. _outfits_cache: list[dict] | None = None 모듈 변수
2. _load_outfits_cached() 함수: 캐시 있으면 deepcopy 반환, 없으면 파일 로드 후 캐시
3. deepcopy 사용 이유: 파이프라인에서 outfit dict를 수정(scores 추가)하므로 원본 보호

주의: import copy 추가. 기존 함수명 _load_outfits_from_json은 내부용으로 유지.
테스트 후 커밋.
```

### Prompt 2-3. CORS 수정

```
backend/app/main.py에서 CORS 설정을 수정해줘.

현재: allow_origins=["*"] (하드코딩)
변경: allow_origins=settings.cors_origins (config.py에서 관리)

backend/app/config.py의 cors_origins 리스트에 다음 도메인이 포함되어 있는지 확인:
- http://localhost:3000
- https://frontend-msunkang70-1055s-projects.vercel.app

allow_credentials=False는 유지.
수정 후 서버 실행해서 /health 엔드포인트 접근 확인.
```

---

## Step 3. 구조 리팩토링 (P1)

### Prompt 3-1. 4단계 파이프라인 분리

```
docs/SYSTEM_REDESIGN_v3.md의 "3. 재설계 구조" 섹션을 읽어.

backend/app/services/feed_builder.py를 리팩토링해줘.

현재 구조:
- apply_hard_filters() → 8개 필터 전부 포함
- score_and_rerank() → scoring + rerank 통합

새 구조 (4단계):

1. stage1_hard_filter(outfits, user_gender, budget_max, current_month) → list[dict]
   - H1(성별), H2(예산), H3(계절)만 포함
   - 객관적 불일치 = 즉시 제거

2. stage2_eligibility(outfits, user_tone_id, user_tpo_list, disliked_ids) → list[dict]
   - H4(TPO), H5(브랜드), H6(LLM품질), H7(톤), H8(StyleFilter)
   - 적합성 게이트 = 후보 압축
   - 최소 보장: 후보 5개 미만이면 톤 기준 완화하여 재시도

3. stage3_soft_score(outfits, user_tone_id, user_tpo_list, budget_min, budget_max, weight_overrides) → list[dict]
   - compute_soft_scores() 호출 + 정렬
   - _adjust_weights_by_data_quality() 적용
   - 제거 절대 금지, 순위만 결정

4. stage4_expert_rerank(outfits, user_tpo_list, preferences, max_results) → list[dict]
   - 완성 코디 가산(+3)
   - 개인화 보정(-10~+10)
   - 톤 다양성 제한 (동일 톤 3개)
   - 메인아이템 중복 제거

기존 apply_hard_filters()와 rerank()는 deprecated wrapper로 유지 (호환성).
기존 개별 필터 함수(filter_h1_gender 등)는 그대로 유지, 호출 위치만 변경.

수정 후 기존 pytest가 모두 통과하는지 확인해줘.
```

### Prompt 3-2. feed.py 파이프라인 연결

```
backend/app/routers/feed.py의 get_feed() 함수를 수정해줘.

현재:
  filtered = apply_hard_filters(...)
  ranked = score_and_rerank(...)

변경:
  # Stage 1: Hard Filter
  hard_filtered = stage1_hard_filter(all_outfits, user_gender=gender, budget_max=budget_max)

  # Stage 2: Eligibility
  eligible = stage2_eligibility(hard_filtered, user_tone_id=tone_id, user_tpo_list=tpo_list)

  # Stage 3: Soft Score
  scored = stage3_soft_score(eligible, user_tone_id=tone_id, user_tpo_list=tpo_list, budget_min=budget_min, budget_max=budget_max)

  # Stage 4: Expert Rerank
  ranked = stage4_expert_rerank(scored, user_tpo_list=tpo_list, max_results=200)

import 경로도 업데이트.
Reason Generation 부분은 변경 없음.
수정 후 서버 실행하여 /api/feed?tone_id=summer_cool_light&tpo=commute&gender=female 응답 확인.
```

### Prompt 3-3. Eligibility 최소 보장 로직

```
backend/app/services/feed_builder.py의 stage2_eligibility()에 최소 보장 로직을 추가해줘.

문제: 필터 조건이 엄격하면 후보가 0개가 될 수 있다 (예: workout TPO + 특정 톤).

로직:
1. 정상 필터링 실행
2. 결과가 5개 미만이면:
   a. 톤 필터(E2) 제거 후 재시도
   b. 여전히 5개 미만이면 TPO 필터(E1)도 제거 후 재시도
   c. 완화된 결과에 [relaxed=True] 플래그 추가
3. 완화 시 로그 출력: f"Eligibility relaxed: {len(candidates)} candidates (tone={tone_relaxed}, tpo={tpo_relaxed})"

이렇게 하면 "조건에 맞는 코디가 없어요" 상태를 최소화할 수 있어.
```

---

## Step 4. 검증

### Prompt 4-1. 데이터 검증

```
다음 검증 스크립트를 만들고 실행해줘.

파일: backend/scripts/verify_data_quality.py

검증 항목:
1. color_hex 채워진 비율 (목표: 90% 이상)
2. 시즌 태그 있는 코디 비율 (목표: 100%)
3. TPO별 코디 수 (workout ≥ 50)
4. 총점(total) 분포: min, max, mean, stdev (목표: stdev > 5)
5. 축별 점수 분포: 각 축의 stdev (목표: CH stdev > 3)
6. 여성/남성 코디 비율
7. 가격 극단값 (700만원 이상 코디 목록)

결과를 표로 깔끔하게 출력.
PASS/FAIL 판정 포함.
```

### Prompt 4-2. 파이프라인 통합 테스트

```
4단계 파이프라인의 통합 테스트를 작성해줘.

파일: backend/tests/test_pipeline_stages.py

테스트 시나리오:

1. test_stage1_removes_wrong_gender
   - 여성 사용자 → 남성 코디 제거 확인

2. test_stage1_removes_over_budget
   - budget_max=100000 → 150001원 이상 코디 제거 확인

3. test_stage2_tpo_matching
   - tpo=commute → commute/office 코디만 통과 확인

4. test_stage2_minimum_guarantee
   - 극단 조건(workout + winter_cool_deep) → 최소 1개 이상 반환 확인

5. test_stage3_no_removal
   - 입력 N개 → 출력 N개 (제거 금지) 확인

6. test_stage3_sorted_by_total
   - 출력이 total 내림차순 확인

7. test_stage4_diversity
   - 동일 톤 코디 10개 입력 → 출력에서 동일 톤 3개 이하 확인

8. test_full_pipeline_e2e
   - 실제 outfits_scored.json 로드 → 4단계 전체 실행 → 결과 5개 이상 확인

pytest 실행하고 결과 알려줘.
```

### Prompt 4-3. 스코어 변별력 검증

```
Step 1 데이터 보강 + Step 2 CH 가중치 수정 후의 스코어 변별력을 검증해줘.

파일: backend/scripts/verify_score_discrimination.py

검증:
1. outfits_scored.json 로드
2. summer_cool_light + commute 조건으로 파이프라인 실행
3. 결과 코디들의 총점 분포 출력
4. Top1 vs Top5 점수 차이
5. Top1 vs Top10 점수 차이
6. 축별 점수 분포 (각 축의 min/max/stdev)

판정 기준:
- Top1과 Top5 차이 ≥ 3점 → PASS
- 각 축 stdev ≥ 3 → PASS
- CH stdev > 0 (color_hex 보강된 경우) → PASS

결과 표로 출력.
```

---

## 실행 체크리스트

```
□ Step 1-1: color_hex 추출 완료 (성공률 90%+)
□ Step 1-2: 시즌 태그 추가 완료 (1,500개 전체)
□ Step 1-3: workout 코디 50개+ 확인
□ Step 2-1: CH 가중치 0 적용 + pytest PASS
□ Step 2-2: JSON 캐싱 적용
□ Step 2-3: CORS 수정
□ Step 3-1: 4단계 함수 분리 + pytest PASS
□ Step 3-2: feed.py 파이프라인 연결 + API 동작 확인
□ Step 3-3: Eligibility 최소 보장 로직
□ Step 4-1: 데이터 검증 PASS
□ Step 4-2: 통합 테스트 PASS
□ Step 4-3: 스코어 변별력 Top1-Top5 ≥ 3점
```

---

## 참고: CLAUDE.md Task 등록용

```
Step 1~4 완료 후 TASK_v3.md에 다음 Task를 추가해줘:

**Task 3.5v3 — 추천 시스템 구조 재정의** ✅ `날짜`
- 목적: 5축 스코어링 변별력 확보 + 4단계 파이프라인 분리
- 수정 파일: feed_builder.py, feed.py, scoring.py, outfits_scored.json
- 작업 내용:
  - [x] color_hex 데이터 보강
  - [x] 시즌 태그 자동 태깅
  - [x] workout TPO 코디 보강 (8→50+)
  - [x] CH 가중치 동적 조정
  - [x] JSON 캐싱 적용
  - [x] 4단계 파이프라인 분리 (Hard→Eligibility→Score→Expert)
  - [x] Eligibility 최소 보장 로직
  - [x] 통합 테스트 작성
- 완료 기준: 스코어 변별력 Top1-Top5 ≥ 3점, pytest 전체 통과
```
