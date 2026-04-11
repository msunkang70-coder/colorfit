# ColorFit 추천 시스템 구조 재정의 및 검증 보고서

**작성일:** 2026-04-02
**대상 코드:** backend/app/services/ (feed_builder, scoring, style_filter, reason_generator)
**버전:** v3 Explore Mode 구현 완료 기준

---

## 1. 현황 요약

현재 ColorFit 추천 시스템은 **Hard Filter(8단계) → Soft Score(5축) → Rerank → Reason** 파이프라인으로 동작한다. 구조 자체는 기획서의 의도를 충실히 반영하고 있으나, **데이터 품질 문제로 인해 5축 스코어링 중 3개 축(CH, PE, OF)이 사실상 무차별 상태**이며, 이는 추천 품질의 근본적 한계를 만든다.

핵심 수치:
- 전체 코디 1,500개, 총점 범위 76.6~81.7 (5점 차이 — 변별력 극히 낮음)
- `color_hex` 필드 전체 비어있음 → CH(색상조화) = 70.0 고정
- OF(TPO적합도) = 80.0 고정 (프리컴퓨팅 시점)
- PE(가격효율) = 70.0 고정 (프리컴퓨팅 시점)
- workout TPO 코디 8개 (서비스 불가 수준)
- 시즌 태그 0개 (H3 필터 항상 통과)

---

## 2. 구조 문제 분석

### 2.1 현재 파이프라인 진단

**질문 1: Hard Filter가 실제로 "제외 조건"으로 작동하는가?**

부분적으로 YES. H1(성별), H2(예산), H4(TPO), H5(브랜드) 필터는 제대로 작동한다. 그러나:
- **H3(시즌):** 전 코디에 시즌 태그가 없어서 항상 통과 — 사실상 비활성
- **H7(톤):** 모든 아이템에 `tone_id`가 있어서 정상 동작하지만, `_get_compatible_tones()`이 60점 이상을 호환으로 판단 → 같은 온도 계열이면 대부분 통과하여 필터링이 느슨함
- **H8(StyleFilter):** SF 55점 이하가 0개 → 사실상 비활성 (모든 코디가 통과)

**질문 2: Soft Score가 제거 역할까지 수행하고 있지는 않은가?**

NO. 현재 구조에서 Soft Score는 순위만 조정하고 제거하지 않는다. 이 부분은 설계 원칙에 부합한다. 그러나 문제는 **변별력이 없어서 순위 조정 자체가 무의미**하다는 것이다.

**질문 3: Rerank가 단순 정렬인지, 전문가 보정 역할을 하고 있는가?**

Rerank는 세 가지 역할을 동시에 수행한다:
1. 완성 코디 가산(+3점) — 보정
2. 톤 다양성 제한(동일 톤 3개) — 필터
3. 메인아이템 중복 제거(1개 제한) — 필터

**역할 혼재:** 2, 3번은 필터링 역할인데 Score 이후 단계에서 수행하고 있다. 설계상 Eligibility Filter에 있어야 할 로직이다.

**질문 4: 퍼스널컬러/TPO/성별이 어느 단계에서 처리되고 있는가?**

| 요소 | 현재 위치 | 처리 방식 |
|------|----------|----------|
| 성별 | H1 (Hard Filter) | 반대 성별 제거 ✅ 적절 |
| 퍼스널컬러 | H7 (Hard Filter) + PCF (Soft Score) | 호환 톤 필터 + 점수화 — H7이 느슨하여 실질적으로 PCF에만 의존 |
| TPO | H4 (Hard Filter) + OF (Soft Score) | 동의어 확장 후 매칭 — 정상적이나 designed_tpo 태깅 품질에 의존 |
| 계절 | H3 (Hard Filter) | 시즌 태그 0개로 비활성 ❌ |
| 예산 | H2 (Hard Filter) + PE (Soft Score) | 1.5배 초과만 제거 + 범위 내 점수화 ✅ |
| 스타일 | H8 (Hard Filter) + SF (Soft Score) | SF 55 미만 제거 + 점수화 — 컷오프 이하가 0개로 비활성 |

### 2.2 문제 분류

#### Hard Filter 실패
- **H3 시즌 필터 비활성:** 시즌 태그가 전혀 없음 → 여름에 패딩 추천 가능
- **H8 StyleFilter 비활성:** 모든 코디가 55점 이상 → 사실상 게이트 없음
- **H7 톤 필터 과도 통과:** 같은 온도 계열이면 대부분 통과

#### 데이터 문제 (가장 심각)
- **`color_hex` 전체 비어있음:** 3,664개 아이템 전부. CH 스코어링 불능, PCF는 tone_id 기반 팔레트로 폴백하지만 RGB 거리 비교 불가
- **시즌 태그 0개:** H3 필터 무력화
- **workout TPO 8개:** 해당 카테고리 서비스 불가
- **남성 코디 696개:** 타겟 사용자가 20대 여성인데 46%가 남성 데이터

#### Score 설계 문제
- **총점 범위 5점(76.6~81.7):** 1,500개 코디가 거의 동점 → 추천 순위가 사실상 랜덤
- **CH = 70.0 고정:** color_hex 없음 → `len(item_hex_colors) < 2` 분기가 아닌, `_hex_to_rgb("")` → `(128,128,128)` 반환 → 동일 색으로 처리되어 고정값
- **OF 프리컴퓨팅 = 80.0 고정:** 모든 코디가 match_count ≥ 2로 평가된 것 (런타임에는 달라짐)
- **PE 프리컴퓨팅 = 70.0 고정:** 배치 시점 예산 설정 문제

#### 구조적 설계 문제
- **Rerank에 필터 로직 혼재:** 톤 다양성 제한 + 메인아이템 중복 제거가 Rerank에 위치
- **프리컴퓨팅 스코어 미활용:** `outfits_scored.json`에 저장된 scores가 있지만, 런타임에서 전체 재계산 → 프리컴퓨팅 의미 없음
- **매 요청마다 1,500개 전체 로드:** 캐싱 없이 파일 I/O + 전체 파이프라인 실행

---

## 3. 재설계 구조

### 3.1 현재 vs 제안

```
현재:  Hard Filter(8) ─→ Soft Score(5축) ─→ Rerank ─→ Reason
          │                    │                │
          ▼                    ▼                ▼
     제거만 수행          순위만 조정      제거+보정 혼재  ← 문제

제안:  Stage 1        Stage 2           Stage 3        Stage 4
       Hard Filter ─→ Eligibility ─→ Soft Score ─→ Expert Rerank
          │              │               │              │
          ▼              ▼               ▼              ▼
       절대 제외      후보 압축       순위 결정      품질 보정
       (위반=즉사)  (적합성 게이트) (제거 금지)   (최종 조율)
```

### Stage 1. Hard Filter (절대 제외)

틀리면 무조건 탈락. 계산 비용 최소.

| ID | 조건 | 현재 상태 | 변경 |
|----|------|----------|------|
| H1 | gender 불일치 | ✅ 정상 | 유지 |
| H2 | budget_max × 1.5 초과 | ✅ 정상 | 유지 |
| H3 | 계절 완전 불일치 | ❌ 시즌 태그 없음 | **데이터 보강 필수** |
| H_stock | 재고 없음 | 미구현 | 추가 (MVP 이후) |
| H_block | 사용자 차단 아이템 | dislike 처리와 중복 | Rerank에서 이관 |

```python
# Stage 1: Hard Filter — 절대 제외만 수행
def stage1_hard_filter(
    outfits: list[dict],
    user_gender: str,
    budget_max: float,
    current_month: int | None = None,
) -> list[dict]:
    """위반 시 무조건 제거. 계산 비용 최소."""
    return [
        o for o in outfits
        if filter_h1_gender(o, user_gender)
        and filter_h2_budget(o, budget_max)
        and filter_h3_season(o, current_month)
    ]
```

### Stage 2. Eligibility Filter (후보군 압축)

적합성 기준으로 후보를 압축. 점수 기반이 아닌 pass/fail.

| ID | 조건 | 현재 위치 | 변경 |
|----|------|----------|------|
| E1 | TPO 매칭 (동의어 확장) | H4 | **이관** (Hard → Eligibility) |
| E2 | 톤 호환성 범위 | H7 | **이관** + 기준 강화 (60→70점) |
| E3 | 브랜드 화이트리스트 | H5 | **이관** |
| E4 | StyleFilter (SF ≥ 55) | H8 | **이관** |
| E5 | LLM 품질 ≥ 3 | H6 | **이관** |
| E6 | 포멀도 일관성 | Rerank(없음) | **신규** |
| E7 | 톤 다양성 제한 | Rerank | **이관** |
| E8 | 메인아이템 중복 제거 | Rerank | **이관** |

**Hard Filter와 Eligibility의 구분 기준:**
- Hard Filter: 객관적 불일치 (성별이 다르다, 예산을 초과한다, 계절이 맞지 않다)
- Eligibility: 주관적/맥락적 적합성 (TPO가 유사한가, 톤이 호환되는가, 스타일이 어울리는가)

```python
# Stage 2: Eligibility Filter — 적합성 게이트
def stage2_eligibility(
    outfits: list[dict],
    user_tone_id: str,
    user_tpo_list: list[str],
    disliked_ids: set[str] | None = None,
) -> list[dict]:
    """적합성 기준 후보 압축. 과잉 제거 방지를 위해 최소 보장 로직 포함."""
    if disliked_ids is None:
        disliked_ids = set()

    candidates = []
    for o in outfits:
        # 사용자 차단 제거
        if o.get("outfit_id", "") in disliked_ids:
            continue
        # E1: TPO 매칭
        if user_tpo_list and not filter_h4_tpo(o, user_tpo_list):
            continue
        # E2: 톤 호환 (기준 70으로 강화)
        if not filter_tone_eligible(o, user_tone_id, threshold=70):
            continue
        # E3: 브랜드
        if not filter_h5_brand(o):
            continue
        # E4: StyleFilter
        style_passed, sf_score, details = filter_h8_style(o)
        if not style_passed:
            continue
        o["style_details"] = details
        # E5: LLM 품질
        if not filter_h6_llm_quality(o):
            continue
        candidates.append(o)

    # 최소 보장: 후보가 너무 적으면 톤 기준 완화
    if len(candidates) < 5 and len(outfits) > 5:
        candidates = _relax_eligibility(outfits, user_tpo_list, disliked_ids)

    return candidates
```

### Stage 3. Soft Score (순위화)

점수는 순위 결정에만 사용. 제거 절대 금지.

| 축 | 이름 | 가중치 | 현재 문제 | 수정 방향 |
|----|------|--------|----------|----------|
| PCF | 퍼스널컬러 적합도 | 0.25 | color_hex 없어 tone_id만 사용 | **color_hex 데이터 보강** |
| OF | TPO 적합도 | 0.20 | 정상 (런타임 재계산) | 유지 |
| CH | 색상 조화도 | 0.15 | **전체 70.0 고정** (color_hex 없음) | **color_hex 보강 전까지 가중치 0으로** |
| PE | 가격 효율성 | 0.15 | 정상 (런타임 재계산) | 유지 |
| SF | 스타일 적합도 | 0.25 | 변별력 낮음 (70~78.8) | silhouette 데이터 보강 |

```python
# Stage 3: Soft Score — 순위만 결정 (제거 금지)
def stage3_soft_score(
    outfits: list[dict],
    user_tone_id: str,
    user_tpo_list: list[str],
    budget_min: float,
    budget_max: float,
    weight_overrides: dict[str, float] | None = None,
) -> list[dict]:
    """5축 스코어링 → 가중합 총점으로 정렬. 제거하지 않는다."""
    # CH 데이터 없으면 가중치 0으로 자동 조정
    effective_weights = _adjust_weights_by_data_quality(outfits, weight_overrides)

    for outfit in outfits:
        scores = compute_soft_scores(
            outfit, user_tone_id, user_tpo_list,
            budget_min, budget_max, effective_weights,
        )
        outfit["scores"] = scores

    outfits.sort(key=lambda o: o["scores"]["total"], reverse=True)
    return outfits


def _adjust_weights_by_data_quality(
    outfits: list[dict],
    overrides: dict[str, float] | None,
) -> dict[str, float]:
    """데이터 품질에 따라 축 가중치를 자동 조정."""
    w = dict(DEFAULT_WEIGHTS)
    if overrides:
        w.update({k: v for k, v in overrides.items() if k in w})

    # color_hex 없으면 CH 가중치 0
    sample = outfits[:10] if outfits else []
    has_color = any(
        item.get("color_hex", "").strip()
        for o in sample for item in o.get("items", [])
    )
    if not has_color:
        w["ch"] = 0.0

    # 정규화
    total = sum(w.values())
    if total > 0:
        w = {k: v / total for k, v in w.items()}
    return w
```

### Stage 4. Expert Rerank (전문가 보정)

최종 품질 조율. 순위 미세 조정만 수행.

| 보정 | 설명 | 점수 |
|------|------|------|
| 완성 코디 가산 | 상의+하의+아우터 | +3점 |
| 개인화 보정 | 톤/카테고리/브랜드 선호 | -10~+10 |
| 코디 조화 보너스 | 색상 대비가 적절한 조합 | +2점 (CH≥80 시) |
| TPO 뉘앙스 보정 | 면접인데 캐주얼 → 감점 | -3점 |
| 과잉/부족 스타일링 | 포멀도 편차 큼 → 감점 | -2점 |

```python
# Stage 4: Expert Rerank — 최종 품질 보정
def stage4_expert_rerank(
    outfits: list[dict],
    user_tpo_list: list[str],
    preferences: dict | None = None,
    max_results: int = 20,
) -> list[dict]:
    """전문가 보정 로직. 순위 미세 조정 + 다양성 보장."""
    for outfit in outfits:
        bonus = 0.0
        scores = outfit.get("scores", {})

        # 완성 코디 가산
        if outfit.get("is_complete_outfit", False):
            bonus += 3.0

        # 개인화 보정
        bonus += _personalization_bonus(outfit, preferences)

        # TPO 뉘앙스: 면접인데 formality 낮으면 감점
        bonus += _tpo_nuance_penalty(outfit, user_tpo_list)

        # 포멀도 편차 감점
        bonus += _formality_consistency_bonus(outfit)

        scores["expert_total"] = round(
            min(scores.get("total", 0) + bonus, 100.0), 2
        )
        outfit["scores"] = scores

    # 최종 정렬
    outfits.sort(
        key=lambda o: o["scores"].get("expert_total", 0), reverse=True
    )

    # 다양성 보장 (톤 다양성 + 메인아이템 중복 제거)
    return _ensure_diversity(outfits, max_results)
```

---

## 4. 요소 매핑 표

| 요소 | Stage 1 (Hard) | Stage 2 (Eligibility) | Stage 3 (Score) | Stage 4 (Expert) |
|------|---------------|----------------------|----------------|-----------------|
| 성별 | ✅ H1 제거 | — | — | — |
| 예산 | ✅ H2 1.5배 초과 제거 | — | PE 점수화 | — |
| 계절 | ✅ H3 반대 시즌 제거 | — | — | — |
| TPO | — | ✅ E1 동의어 매칭 | OF 점수화 | TPO 뉘앙스 보정 |
| 퍼스널컬러 | — | ✅ E2 톤 호환 범위 | PCF 점수화 | — |
| 브랜드 | — | ✅ E3 화이트리스트 | — | 브랜드 선호 보정 |
| 스타일 | — | ✅ E4 SF≥55 | SF 점수화 | 과잉/부족 보정 |
| LLM 품질 | — | ✅ E5 ≥3점 | — | — |
| 포멀도 | — | E6 일관성 체크 | SF 내 포멀도 점수 | 포멀도 편차 감점 |
| 톤 다양성 | — | — | — | ✅ 다양성 보장 |
| 아이템 중복 | — | — | — | ✅ 중복 제거 |
| 개인 선호 | — | — | — | ✅ ±10 보정 |
| 나이/라이프스테이지 | — | (향후 E-new) | — | (향후 보정) |
| 전문가 추천 | — | — | — | ✅ 조화/뉘앙스 |

---

## 5. 코드 적용 방향

### 5.1 현재 코드에서 잘못된 단계에 있는 요소

| 요소 | 현재 위치 | 올바른 위치 | 이유 |
|------|----------|------------|------|
| TPO 필터 (H4) | Hard Filter | Eligibility | TPO 불일치는 "절대 불가"가 아니라 "덜 적합" |
| 톤 필터 (H7) | Hard Filter | Eligibility | 톤 호환성은 연속적, 이진 판단 부적절 |
| 브랜드 필터 (H5) | Hard Filter | Eligibility | 브랜드 미포함이 "위반"은 아님 |
| 톤 다양성 제한 | Rerank | Expert Rerank | 다양성은 보정이지 순위가 아님 |
| 메인아이템 중복 제거 | Rerank | Expert Rerank | 중복 제거는 품질 보정 |
| dislike 제외 | Rerank | Eligibility | 사용자 차단은 가능한 빨리 제외 |

### 5.2 역할이 혼재된 지점

**feed_builder.py `apply_hard_filters()`:**
현재 H1~H8이 모두 하나의 함수에서 순차 실행되는데, H4(TPO), H5(브랜드), H7(톤)은 Hard가 아닌 Eligibility 성격이다.

**feed_builder.py `rerank()`:**
dislike 제외 + 완성 코디 가산 + 개인화 보정 + 톤 다양성 + 메인아이템 중복이 하나의 함수에 혼재. 이 중 dislike 제외는 필터, 다양성/중복은 Expert Rerank에 분리해야 한다.

### 5.3 파이프라인 구조 제안

```python
# feed.py — 새 파이프라인
@router.get("/feed", response_model=FeedResponse)
async def get_feed(...) -> FeedResponse:
    all_outfits = _load_outfits_cached()  # 캐싱 적용

    # Stage 1: Hard Filter (절대 제외)
    filtered = stage1_hard_filter(
        all_outfits, user_gender=gender,
        budget_max=budget_max, current_month=None,
    )

    # Stage 2: Eligibility (후보 압축)
    eligible = stage2_eligibility(
        filtered, user_tone_id=tone_id,
        user_tpo_list=tpo_list, disliked_ids=None,
    )

    # Stage 3: Soft Score (순위 결정)
    scored = stage3_soft_score(
        eligible, user_tone_id=tone_id,
        user_tpo_list=tpo_list,
        budget_min=budget_min, budget_max=budget_max,
    )

    # Stage 4: Expert Rerank (품질 보정)
    ranked = stage4_expert_rerank(
        scored, user_tpo_list=tpo_list,
        max_results=page_size * 2,  # 여유분
    )

    # Pagination + Reason Generation
    page_outfits = ranked[start:end]
    for outfit in page_outfits:
        outfit["reasons"] = generate_reasons(
            outfit["scores"], items=outfit["items"],
            user_tone_id=tone_id, user_tpo_list=tpo_list,
        )

    return FeedResponse(...)
```

### 5.4 파일 수정 범위

| 파일 | 변경 내용 |
|------|----------|
| `services/feed_builder.py` | `apply_hard_filters()` → `stage1_hard_filter()` + `stage2_eligibility()` 분리 |
| `services/feed_builder.py` | `rerank()` → `stage4_expert_rerank()` 리팩토링 |
| `services/feed_builder.py` | `_adjust_weights_by_data_quality()` 신규 추가 |
| `services/scoring.py` | CH 가중치 0 처리 로직 (color_hex 없을 때) |
| `routers/feed.py` | 4단계 파이프라인 호출 구조 변경 |
| `routers/feed.py` | `_load_outfits_cached()` 캐싱 추가 |

---

## 6. 우선순위 개선안

### P0 — 신뢰 붕괴 문제 (즉시)

| # | 문제 | 영향 | 수정 |
|---|------|------|------|
| P0-1 | `color_hex` 전체 비어있음 | CH 스코어 무력화, PCF RGB 비교 불가 → 5축 중 2축이 사실상 죽음 | color_hex 데이터 보강 (네이버 상품 이미지에서 대표색 추출 스크립트) |
| P0-2 | 시즌 태그 0개 | H3 필터 비활성 → 여름에 패딩 추천 가능 | 카테고리/상품명 기반 시즌 자동 태깅 스크립트 |
| P0-3 | workout TPO 8개 | 운동 탭 선택 시 "코디 없음" | workout 코디 50개 이상 보강 |
| P0-4 | 총점 범위 5점 (76.6~81.7) | Top1과 Top5 차이가 없음 → 추천 = 랜덤 | CH 가중치 0 처리 + 나머지 축 가중치 재분배 (즉시 적용 가능) |

### P1 — 추천 품질 문제 (이번 주)

| # | 문제 | 수정 |
|---|------|------|
| P1-1 | TPO가 Hard Filter에 위치 | Eligibility로 이동 + 매칭 실패 시 관련 TPO 폴백 |
| P1-2 | Rerank에 필터 로직 혼재 | 톤 다양성/메인아이템 중복을 Expert Rerank로 분리 |
| P1-3 | 매 요청마다 JSON 전체 로드 | 모듈 레벨 캐싱 |
| P1-4 | CORS `allow_origins=["*"]` | `settings.cors_origins` 사용 |
| P1-5 | Eligibility 최소 보장 없음 | 후보 5개 미만이면 기준 완화 |

### P2 — 성능 / 확장성 문제 (W4~W5)

| # | 문제 | 수정 |
|---|------|------|
| P2-1 | 1,500개 전체 파이프라인 | 캐싱 + Stage1 결과 캐싱 (gender/season 기준) |
| P2-2 | 프리컴퓨팅 스코어 미활용 | Stage3에서 프리컴퓨팅 + 사용자별 delta만 계산 |
| P2-3 | `next/image` 미사용 | 이미지 최적화 적용 |
| P2-4 | 남성 데이터 46% | 여성 전용 서비스면 남성 데이터 분리 |

---

## 7. UI 흐름 기반 검증

### 온보딩 → 추천 → 비교 → 재선택 → 결정

| 단계 | 적용 필터 | 유지 값 | 변경 가능 값 |
|------|----------|---------|------------|
| 온보딩 완료 | — | gender, tone_id, tpo_list, budget_min/max, style_moods | — |
| 피드 진입 | Stage 1~4 전체 | 위 전체 | activeTpo (탭 선택) |
| TPO 탭 변경 | Stage 1~4 재실행 | gender, tone_id, budget | activeTpo 변경 → 새 피드 |
| 예산 변경 | Stage 1~4 재실행 | gender, tone_id, activeTpo | budget_min/max |
| "비슷한 선택 보기" | 프론트 로직만 (selectDiverseTop3) | 백엔드 결과 유지 | expandLevel 0→1 |
| compact 카드 탭 | 프론트 상태만 | allOutfits 유지 | decision 교체, selectedRank 변경 |
| "이걸로 결정" | — | — | 설문 팝업 → 외부 이동 |
| "다른 제안 보기" | Stage 1~4 재실행 (다른 페이지) | 모든 설정 유지 | page 변경 |

**현재 문제:**
- TPO 탭 변경 시 `expandLevel`이 0으로 리셋 ✅ (정상)
- "전체" 탭 선택 시 빈 문자열 → `p.tpo_list.join(",")` 폴백 → 의미 모호

---

## 8. 데이터 구조 문제 분석

### outfits_scored.json 진단 결과

| 항목 | 현재 상태 | 심각도 | 조치 |
|------|----------|--------|------|
| color_hex | **전체 비어있음** (3,664 아이템) | 🔴 Critical | 네이버 이미지 → 대표색 추출 배치 |
| 시즌 태그 | **0개** | 🔴 Critical | 카테고리+상품명 기반 자동 태깅 |
| workout TPO | **8개** | 🔴 Critical | 코디 데이터 50개 이상 보강 |
| 남성 코디 비율 | 696/1500 (46%) | 🟡 Warning | 여성 전용이면 분리 저장 |
| tone_id 커버리지 | 12톤 전체 99~137개 | ✅ Good | — |
| items 구성 | 2~5개 (2개 60%, 3개 35%) | ✅ Good | — |
| 가격 범위 | 21,200~7,072,562 | 🟡 Warning | 극단값 필터 필요 |
| LLM 품질 | 3점 328개, 4점 1172개 | ✅ Good | — |
| gender 아이템 불일치 | 0개 | ✅ Good | — |
| designed_tpo 커버리지 | 전체 있음 | ✅ Good | — |

---

## 9. 최종 평가

### "현재 시스템은 사용자가 신뢰하고 결정을 내릴 수 있는 수준인가?"

**아니다. 현재 시스템은 "무작위에 가까운 추천"을 하고 있다.**

근거:
1. **총점 변별력 5점** — 1,500개 코디가 76.6~81.7 범위에 몰려 있다. Top1과 Top10의 차이가 1~2점이다. 이는 사실상 랜덤 정렬과 동일하다.
2. **5축 중 2축(CH, PCF-RGB) 비작동** — color_hex가 비어있어 색상 기반 추천이 불가능하다. 퍼스널컬러 서비스인데 색상 데이터가 없는 것은 치명적이다.
3. **시즌 필터 비활성** — 4월에 겨울 패딩이 추천될 수 있다.
4. **"왜 이 코디인지" 설명이 데이터에 기반하지 않음** — evidence가 축 점수 기반인데, 축 점수 자체가 무의미하면 evidence도 무의미하다.

**그러나 구조적 기반은 충분하다.** 파이프라인 설계(Filter→Score→Rerank→Reason), 이유 생성 3파트 구조, 프론트엔드 UX(Decision/Explore Mode), 측정 시스템은 모두 잘 설계되어 있다.

**가장 시급한 것은 코드 변경이 아니라 데이터 보강이다:**
1. `color_hex` 채우기 → CH 스코어 활성화 + PCF RGB 비교 활성화
2. 시즌 태그 채우기 → H3 필터 활성화
3. workout 코디 보강 → 전 TPO 서비스 가능

이 세 가지를 처리하면 현재 코드 구조만으로도 추천 품질이 극적으로 개선된다.

### 절대 기준 검증

| 기준 | 현재 상태 | 판정 |
|------|----------|------|
| 성별 불일치 | H1 필터 정상, 아이템 레벨 불일치 0개 | ✅ PASS |
| 계절 불일치 | 시즌 태그 0개 → 필터 비활성 | ❌ FAIL |
| TPO 불일치 | H4 필터 + OF 스코어 정상 동작 | ✅ PASS (단, workout 데이터 부족) |

**최종 판정: CONDITIONAL FAIL — 데이터 보강 시 PASS 전환 가능**
