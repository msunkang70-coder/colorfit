# ColorFit 종합 수정 — Claude Code 실행 프롬프트 v3

## 근본 원인 분석 (스크린샷 기반)

```
문제 1: 출근탭에 민트 가디건, 남성 바지 표시
  → 원인: score 범위 76.6~81.7 (stdev 0.7) — 점수 변별력 0, 사실상 랜덤 정렬
  → 원인: stage2_eligibility에서 최소 5개 보장 위해 TPO 필터 완화 → TPO 무관 코디 유입

문제 2: 남성용 베이지 치노 + 검정 조거 → 여성 사용자에게 표시
  → 원인: stage1_hard_filter에서 gender 필터는 아이템 레벨로 체크하지만,
           outfit 레벨 gender 필드를 무시. 또한 eligibility 완화 시 gender 재검증 없음

문제 3: "비슷한 선택"이 앵커 코디와 무관
  → 원인: selectDiverseTop3()가 "다른 축" 기준으로 선발 — 앵커와 유사한 코디가 아니라
           앵커와 다른 강점의 코디를 선택. TPO/시즌/분위기 유사성 무시

문제 4: 4월에 겨울 롱패딩 표시
  → 원인: 1448개 코디 중 332개가 ALL 4시즌 태그, 823개가 3시즌 태그
           → H3 시즌 필터 사실상 무력화 (80% 코디가 현재 시즌 포함)

문제 5: 면접탭에 초록 벨벳 롱드레스 표시
  → 원인: designed_tpo=["interview"]는 맞지만, 포멀도/아이템 적합성 검증 없음
           면접에 부적절한 원피스가 데이터에 9개 존재하며, 점수 변별력 0이라 상위 노출

문제 6: feed.py 133줄에서 잘림 (return문 없음), feed_builder.py에 rerank/score_and_rerank 미정의
  → 파이프라인 실행 자체가 불완전
```

## 실행 순서

```
STEP 0 (파일 복원)  → STEP 1 (데이터)  → STEP 2 (추천 구조)  → STEP 3 (비슷한 선택)
       │                    │                    │                     │
  잘린 파일 완성       시즌태그 정제        변별력 확보           앵커 기반 유사도
  import 오류 수정     포멀도 검증         TPO 매칭 강화

→ STEP 4 (스타일리스트 룰)  → STEP 5 (UI)  → STEP 6 (QA 레이어)
         │                       │                  │
    TPO별 금기 적용          멀티아이템 표시     사전 검증 게이트
    면접/출근 룰              탭바 축소          성별/시즌/TPO 크로스체크
```

---

## STEP 0. 파일 무결성 복원 (Critical — 먼저 실행)

```
feed.py와 feed_builder.py가 잘려있어. 먼저 복원해줘.

### 1. backend/app/routers/feed.py (133줄에서 잘림)

현재 `for outfit in page_outfits:` 이후가 없어. 아래를 추가:

```python
    for outfit in page_outfits:
        items = outfit.get("items", [])
        scores = outfit.get("scores", {})
        reasons = generate_reasons(items, scores, tone_id, tpo_list)
        outfit["reasons"] = reasons

    result_outfits = [_outfit_to_response(o) for o in page_outfits]

    return FeedResponse(
        outfits=result_outfits,
        total_count=total_count,
        page=page,
        page_size=page_size,
        has_next=end < total_count,
    )
```

### 2. backend/app/services/feed_builder.py (492줄에서 잘림)

`_personalization_bonus` 함수가 미완성이고, `rerank`와 `score_and_rerank` 함수가 없어.
아래를 추가:

```python
def _personalization_bonus(outfit: dict, preferences: dict | None) -> float:
    """사용자 선호 톤/카테고리/브랜드 일치에 따른 보정 (-10 ~ +10)."""
    if not preferences:
        return 0.0
    bonus = 0.0
    liked_categories = set(preferences.get("liked_categories", []))
    liked_brands = set(preferences.get("liked_brands", []))
    for item in outfit.get("items", []):
        if item.get("category", "") in liked_categories:
            bonus += 2.0
        if item.get("brand", "").lower() in liked_brands:
            bonus += 2.0
    return min(max(bonus, -10.0), 10.0)


def rerank(
    outfits: list[dict],
    preferences: dict | None = None,
    max_results: int = 200,
) -> list[dict]:
    """Expert Rerank: 완성 코디 가산 + 메인아이템 중복 제거 + 개인화 보정."""
    seen_main_items: set[str] = set()
    result: list[dict] = []

    for outfit in outfits:
        # 메인아이템(items[0]) 중복 제거
        main_id = ""
        items = outfit.get("items", [])
        if items:
            main_id = items[0].get("product_id", "")
        if main_id and main_id in seen_main_items:
            continue
        if main_id:
            seen_main_items.add(main_id)

        # 완성 코디 가산 (+3)
        scores = outfit.get("scores", {})
        bonus = 3.0 if outfit.get("is_complete_outfit") else 0.0
        bonus += _personalization_bonus(outfit, preferences)
        scores["reranked_total"] = scores.get("total", 0) + bonus
        outfit["scores"] = scores

        result.append(outfit)
        if len(result) >= max_results:
            break

    # reranked_total 기준 재정렬
    result.sort(key=lambda o: o.get("scores", {}).get("reranked_total", 0), reverse=True)
    return result


def score_and_rerank(
    outfits: list[dict],
    user_tone_id: str = "",
    user_tpo_list: list[str] | None = None,
    budget_min: float = 0,
    budget_max: float = 300000,
    preferences: dict | None = None,
    max_results: int = 200,
) -> list[dict]:
    """Soft Score + Expert Rerank 통합 (레거시 호환용)."""
    scored = stage3_soft_score(
        outfits, user_tone_id, user_tpo_list, budget_min, budget_max,
    )
    return rerank(scored, preferences, max_results)
```

### 3. 검증
```bash
cd backend && python -c "from app.services.feed_builder import score_and_rerank, rerank; print('OK')"
cd backend && python -c "from app.routers.feed import router; print('OK')"
```

수정 후 npm run build (frontend) + python import 검증 (backend) 실행.
```

---

## STEP 1. 데이터 클렌징 + 시즌 태그 정제 (P0)

```
outfits_scored.json 데이터 품질이 추천 실패의 근본 원인이야.
특히 시즌 태그가 과잉 (332개가 4시즌 모두 보유, 823개가 3시즌) → H3 필터 무력화.

파일: backend/scripts/clean_and_refine_data.py

### 1단계: 시즌 태그 정제 (가장 중요)

현재 문제: tags 배열에 spring, summer, autumn, winter가 과잉 포함
목표: 각 코디의 실제 착용 가능 시즌만 남기기

규칙:
- 아이템 카테고리/이름 기반 시즌 재산정:
  - 겨울 전용: 패딩, 롱패딩, 기모, 퍼코트, 무스탕, 울코트, 터틀넥, 방한 → ["winter"]
  - 여름 전용: 민소매, 반팔, 린넨, 크롭탑, 슬리브리스, 나시, 숏팬츠 → ["summer"]
  - 봄가을: 가디건, 자켓, 블레이저, 트렌치코트 → ["spring", "autumn"]
  - 사계절: 슬랙스, 셔츠, 블라우스, 스커트, 청바지, 로퍼, 힐 → ["spring", "summer", "autumn", "winter"]
- 코디의 시즌 = 아이템 시즌의 교집합 (가장 제한적인 아이템 기준)
  - 예: 울코트(winter) + 슬랙스(사계절) → 코디는 ["winter"]
  - 예: 가디건(spring,autumn) + 스커트(사계절) → 코디는 ["spring", "autumn"]
- 교집합이 비면 union 사용 (fallback)

### 2단계: 포멀도 검증

- 면접(interview) 코디: 모든 아이템 formality >= 4 필수
  - formality 3 이하 아이템 포함 시 designed_tpo에서 interview 제거
- 출근(commute) 코디: 평균 formality >= 3.5
  - 미달 시 designed_tpo에서 commute 제거
- 데이트(date), 캠퍼스(campus), 주말(weekend): formality 제한 없음

### 3단계: 기존 클렌징 (유지)

- 아동복 키워드: 키즈, 아동, 유아, 주니어, kids, baby, 베이비
- 아동복 브랜드: 밍크뮤, 래핑차일드, 블루독, 모이몰른, 알로봇
- 가격: total_price > 2,000,000원 또는 < 10,000원 제거
- 이미지: items[].image_url 비어있는 아이템이 있는 코디 제거
- 단품 코디: 아이템 1개인데 원피스/점프수트 아닌 것 제거

### 4단계: 성별 크로스체크

- outfit.gender와 모든 items[].gender 일치 확인
- 불일치 있으면 (female 코디에 male 아이템) 해당 코디 제거

### 출력

실행 후 출력:
- 시즌 태그 변경: 4시즌→2시즌 이하로 줄어든 코디 수
- 시즌별 분포 (변경 전 vs 변경 후)
- TPO 제거: interview에서 제거된 코디 수, commute에서 제거된 수
- 아동복/가격/이미지 제거 수
- 성별 크로스체크 제거 수
- 남은 코디 수, TPO별 분포

원본 백업: outfits_scored_backup_{timestamp}.json
결과 저장: outfits_scored.json 덮어쓰기

중요: 캐시 무효화를 위해 backend/app/routers/feed.py의 _outfits_cache = None으로 리셋하는 코드도 추가 (서버 재시작 시 자동 반영되지만 명시적으로).
```

---

## STEP 2. 추천 시스템 점수 변별력 확보 (P0)

```
현재 total score 범위가 76.6~81.7 (5점, stdev 0.7)이라 랭킹이 사실상 랜덤이야.
원인: OF=80 고정, CH=70 고정, PE=70 고정 → 3개 축이 상수.

backend/app/services/scoring.py를 수정해줘.

### 1. calculate_of() 개선 — TPO 매칭 변별력 확보

현재: designed_tpo에 사용자 TPO가 있으면 80, 없으면 30 (2단계)
변경: 매칭 깊이에 따라 5단계 차등

```python
def calculate_of(outfit_tags: list[str], user_tpo_list: list[str]) -> float:
    if not user_tpo_list:
        return 50.0

    outfit_tpo = {t.lower() for t in outfit_tags}
    user_tpo = {t.lower() for t in user_tpo_list}

    # 1. 직접 매칭 (designed_tpo에 정확히 일치)
    direct_match = outfit_tpo & user_tpo
    if direct_match:
        return 100.0

    # 2. 동의어 매칭
    user_expanded = set()
    for tpo in user_tpo:
        user_expanded.update(TPO_SYNONYMS.get(tpo, {tpo}))

    synonym_match = outfit_tpo & user_expanded
    if synonym_match:
        return 85.0

    # 3. 분위기 유사 매칭 (같은 그룹)
    TPO_GROUPS = {
        "formal": {"interview", "office", "commute", "meeting"},
        "casual": {"weekend", "casual", "daily", "campus"},
        "special": {"date", "event", "party"},
        "outdoor": {"travel", "workout", "outdoor"},
    }
    user_groups = set()
    for tpo in user_tpo:
        for group, members in TPO_GROUPS.items():
            if tpo in members:
                user_groups.add(group)
    outfit_groups = set()
    for tpo in outfit_tpo:
        for group, members in TPO_GROUPS.items():
            if tpo in members:
                outfit_groups.add(group)

    if user_groups & outfit_groups:
        return 65.0

    # 4. 완전 불일치
    return 30.0
```

### 2. calculate_ch() 개선 — color_hex 활용

STEP 1 이후 color_hex가 있는 데이터 기준으로:

```python
def calculate_ch(hex_colors: list[str]) -> float:
    valid = [h for h in hex_colors if h and h != "#808080" and len(h) >= 4]
    if len(valid) < 2:
        return 60.0  # 기본값을 70→60으로 낮춰서 변별력 확보

    # RGB 변환 + 거리 계산
    rgbs = [_hex_to_rgb(h) for h in valid]
    distances = []
    for i in range(len(rgbs)):
        for j in range(i + 1, len(rgbs)):
            d = sum((a - b) ** 2 for a, b in zip(rgbs[i], rgbs[j])) ** 0.5
            distances.append(d)

    avg_dist = sum(distances) / len(distances)
    MAX_DIST = 441.67  # sqrt(255^2 * 3)

    # 적정 거리 (60~180)에서 최고점, 너무 가깝거나 멀면 감점
    if avg_dist < 30:
        score = 50 + (avg_dist / 30) * 30  # 50~80
    elif avg_dist <= 180:
        score = 80 + (1 - abs(avg_dist - 100) / 80) * 20  # 80~100
    else:
        score = max(30, 80 - (avg_dist - 180) / (MAX_DIST - 180) * 50)  # 30~80

    return round(score, 2)
```

### 3. calculate_pe() 개선 — 예산 중심 변별력

현재: budget 범위 안이면 70 고정
변경: 예산 대비 위치에 따라 연속 점수

```python
def calculate_pe(total_price: int, budget_min: float, budget_max: float) -> float:
    if budget_max <= 0:
        return 70.0

    if total_price <= 0:
        return 50.0

    # 예산 중심값 대비 위치
    budget_mid = (budget_min + budget_max) / 2
    budget_range = budget_max - budget_min if budget_max > budget_min else budget_max

    if total_price <= budget_min:
        # 예산보다 저렴: 가성비 좋지만 너무 싸면 불안
        ratio = total_price / budget_min if budget_min > 0 else 1.0
        return round(70 + ratio * 20, 2)  # 70~90
    elif total_price <= budget_mid:
        # sweet spot
        return round(85 + (1 - (total_price - budget_min) / (budget_mid - budget_min + 1)) * 15, 2)  # 85~100
    elif total_price <= budget_max:
        # 예산 내 상위
        ratio = (total_price - budget_mid) / (budget_max - budget_mid + 1)
        return round(85 - ratio * 15, 2)  # 70~85
    elif total_price <= budget_max * 1.5:
        # 예산 약간 초과
        ratio = (total_price - budget_max) / (budget_max * 0.5 + 1)
        return round(70 - ratio * 30, 2)  # 40~70
    else:
        return 30.0
```

### 4. 가중치 재조정

feed_builder.py의 DEFAULT_WEIGHTS 변경:
```python
DEFAULT_WEIGHTS = {
    "pcf": 0.20,  # 0.25 → 0.20
    "of": 0.30,   # 0.20 → 0.30 (TPO 매칭이 가장 중요)
    "ch": 0.10,   # 0.15 → 0.10
    "pe": 0.15,   # 유지
    "sf": 0.25,   # 유지
}
```

### 5. 검증

수정 후 테스트:
```python
# backend/tests/test_score_discrimination.py
"""점수 변별력 테스트"""
import json
import statistics

def test_score_range():
    """total score 범위가 최소 15점 이상이어야 한다."""
    with open("backend/data/outfits_scored.json") as f:
        data = json.load(f)
    # 여기서 scoring 함수를 호출하여 재계산
    # ... (실제 테스트에서 전체 파이프라인 실행)
    # assert max_score - min_score >= 15
    # assert stdev >= 3.0

def test_of_discrimination():
    """OF 점수가 최소 3단계 이상 분포해야 한다."""
    scores = set()
    # commute 코디를 commute TPO로 계산 → 100
    # commute 코디를 interview TPO로 계산 → 65 (같은 formal 그룹)
    # commute 코디를 date TPO로 계산 → 30 (다른 그룹)
    assert len(scores) >= 3
```

수정 후:
- pytest backend/tests/ 실행
- 점수 분포 출력 (min, max, mean, stdev)
- TPO별 OF 점수 분포 확인
```

---

## STEP 3. "비슷한 선택" 로직 재설계 (P1)

```
현재 selectDiverseTop3()는 "다른 축 강점" 기준이라 앵커 코디와 무관한 코디가 노출돼.
면접 코디를 보는데 캐주얼 코디가 "비슷한 선택"으로 나오면 안 돼.

frontend/app/feed/page.tsx의 selectDiverseTop3() 함수를 수정해줘.

### 변경 방향

기존: 축 다양성 (서로 다른 topAxis)
변경: 앵커 유사성 + 축 다양성

```typescript
function selectDiverseTop3(outfits: FeedOutfit[]): RankedOutfit[] {
  if (outfits.length === 0) return [];

  const top1 = outfits[0];
  const top1Axis = getTopAxis(top1.scores);
  const result: RankedOutfit[] = [
    { outfit: top1, topAxis: top1Axis, label: "1위 추천", rank: 1 },
  ];

  if (outfits.length === 1) return result;

  // 앵커(Top1) 기준 유사도 계산
  const candidates = outfits.slice(1).map(o => ({
    outfit: o,
    axis: getTopAxis(o.scores),
    similarity: calcSimilarity(top1, o),
  }));

  // 유사도 0.5 이상만 후보 (같은 TPO/시즌/분위기)
  const similar = candidates.filter(c => c.similarity >= 0.5);
  const pool = similar.length >= 2 ? similar : candidates;

  // pool 내에서 축 다양성 선발
  const usedAxes = new Set([top1Axis]);
  const usedIds = new Set([top1.outfit_id]);

  // Top2: 다른 축 우선
  const diffAxis = pool.find(c => !usedAxes.has(c.axis) && !usedIds.has(c.outfit.outfit_id));
  if (diffAxis) {
    result.push({ outfit: diffAxis.outfit, topAxis: diffAxis.axis, label: AXIS_LABELS[diffAxis.axis] ?? diffAxis.axis, rank: 2 });
    usedAxes.add(diffAxis.axis);
    usedIds.add(diffAxis.outfit.outfit_id);
  } else if (pool.length > 0) {
    const fallback = pool.find(c => !usedIds.has(c.outfit.outfit_id));
    if (fallback) {
      result.push({ outfit: fallback.outfit, topAxis: fallback.axis, label: AXIS_LABELS[fallback.axis] ?? fallback.axis, rank: 2 });
      usedIds.add(fallback.outfit.outfit_id);
    }
  }

  // Top3: 나머지에서 다른 축
  const remaining = pool.filter(c => !usedIds.has(c.outfit.outfit_id));
  const diffAxis3 = remaining.find(c => !usedAxes.has(c.axis));
  if (diffAxis3) {
    result.push({ outfit: diffAxis3.outfit, topAxis: diffAxis3.axis, label: AXIS_LABELS[diffAxis3.axis] ?? diffAxis3.axis, rank: 3 });
  } else if (remaining.length > 0) {
    result.push({ outfit: remaining[0].outfit, topAxis: remaining[0].axis, label: AXIS_LABELS[remaining[0].axis] ?? remaining[0].axis, rank: 3 });
  }

  return result;
}

function calcSimilarity(anchor: FeedOutfit, candidate: FeedOutfit): number {
  let score = 0;
  const maxScore = 4;

  // 1. 같은 TPO (tags에서 TPO 추출)
  const tpoSet = new Set(["commute", "interview", "date", "weekend", "campus", "travel", "event", "workout"]);
  const anchorTpo = anchor.tags?.filter(t => tpoSet.has(t)) ?? [];
  const candTpo = candidate.tags?.filter(t => tpoSet.has(t)) ?? [];
  if (anchorTpo.some(t => candTpo.includes(t))) score += 1.5;

  // 2. 같은 시즌
  const seasonSet = new Set(["spring", "summer", "autumn", "winter"]);
  const anchorSeason = anchor.tags?.filter(t => seasonSet.has(t)) ?? [];
  const candSeason = candidate.tags?.filter(t => seasonSet.has(t)) ?? [];
  if (anchorSeason.some(t => candSeason.includes(t))) score += 1.0;

  // 3. 비슷한 가격대 (±30%)
  if (anchor.total_price > 0 && candidate.total_price > 0) {
    const ratio = candidate.total_price / anchor.total_price;
    if (ratio >= 0.7 && ratio <= 1.3) score += 0.5;
  }

  // 4. 같은 분위기 (mood tags)
  const moodTags = anchor.tags?.filter(t => !tpoSet.has(t) && !seasonSet.has(t)) ?? [];
  const candMoods = candidate.tags?.filter(t => !tpoSet.has(t) && !seasonSet.has(t)) ?? [];
  if (moodTags.some(t => candMoods.includes(t))) score += 1.0;

  return score / maxScore;
}
```

### OutfitCard에 tags 전달

feed/page.tsx에서 OutfitCard 호출 시 tags가 전달되는지 확인.
FeedOutfit 인터페이스에 tags: string[] 필드가 있는지 확인하고 없으면 추가.

### 검증

npm run build 성공 확인.
비슷한 선택 3개가 모두 같은 TPO인지 콘솔 로그로 확인:
```typescript
console.log("Top3 TPOs:", result.map(r => r.outfit.tags?.filter(t => tpoSet.has(t))));
```
```

---

## STEP 4. 스타일리스트 룰 — TPO별 금기/필수 (P1)

```
면접에 벨벳 드레스, 출근에 오버사이즈 캐주얼이 나오는 건 스타일리스트 관점에서 부적절해.
TPO별 제약 조건을 추가해줘.

파일: backend/app/services/stylist_rules.py (신규 생성)

```python
"""
스타일리스트 룰 — TPO별 아이템 제약 조건.
feed_builder의 stage2_eligibility 이후, stage3_soft_score 이전에 적용.
"""

from __future__ import annotations
from typing import Any

# TPO별 금기 카테고리 (이 카테고리 포함 코디는 해당 TPO에서 제외)
TPO_FORBIDDEN_CATEGORIES: dict[str, set[str]] = {
    "interview": {
        "크롭탑", "민소매", "숏팬츠", "반바지", "후드", "맨투맨",
        "레깅스", "샌들", "슬리퍼", "스니커즈", "패딩", "점퍼",
    },
    "commute": {
        "크롭탑", "숏팬츠", "반바지", "슬리퍼", "레깅스",
        "패딩",  # 겨울 패딩은 시즌 필터에서 처리
    },
    "workout": set(),  # 제한 없음
    "date": {"슬리퍼"},
    "campus": set(),
    "weekend": set(),
    "travel": set(),
    "event": {"후드", "맨투맨", "슬리퍼"},
}

# TPO별 최소 포멀도
TPO_MIN_FORMALITY: dict[str, float] = {
    "interview": 4.0,     # 전 아이템 4 이상
    "commute": 3.5,       # 평균 3.5 이상
    "event": 3.5,         # 평균 3.5 이상
    "date": 3.0,
    "campus": 2.0,
    "weekend": 2.0,
    "travel": 2.0,
    "workout": 1.0,
}

# TPO별 금기 키워드 (아이템 name에 포함 시 제외)
TPO_FORBIDDEN_KEYWORDS: dict[str, list[str]] = {
    "interview": ["벨벳", "시스루", "크롭", "오버사이즈", "빈티지", "찢어진", "디스트로이드"],
    "commute": ["시스루", "크롭", "찢어진"],
}


def check_stylist_rules(outfit: dict, tpo: str) -> tuple[bool, str]:
    """코디가 해당 TPO의 스타일리스트 룰을 통과하는지 검사.

    Returns:
        (passed, reason) — passed=False이면 reason에 탈락 사유
    """
    items = outfit.get("items", [])
    if not items:
        return False, "아이템 없음"

    tpo_lower = tpo.lower()

    # 1. 금기 카테고리 체크
    forbidden_cats = TPO_FORBIDDEN_CATEGORIES.get(tpo_lower, set())
    for item in items:
        cat = item.get("category", "")
        if cat in forbidden_cats:
            return False, f"{tpo}에 부적절한 카테고리: {cat}"

    # 2. 포멀도 체크
    min_formality = TPO_MIN_FORMALITY.get(tpo_lower, 2.0)
    formalities = [item.get("formality", 3) for item in items]

    if tpo_lower == "interview":
        # 면접: 전 아이템 최소 포멀도 이상
        if any(f < min_formality for f in formalities):
            return False, f"면접 코디에 포멀도 {min(formalities)} 아이템 포함 (최소 {min_formality})"
    else:
        # 나머지: 평균 포멀도
        avg = sum(formalities) / len(formalities)
        if avg < min_formality:
            return False, f"{tpo} 평균 포멀도 {avg:.1f} (최소 {min_formality})"

    # 3. 금기 키워드 체크
    forbidden_kw = TPO_FORBIDDEN_KEYWORDS.get(tpo_lower, [])
    for item in items:
        name = item.get("name", "")
        for kw in forbidden_kw:
            if kw in name:
                return False, f"{tpo}에 부적절한 키워드 '{kw}' in '{name[:30]}'"

    return True, ""


def apply_stylist_rules(outfits: list[dict], user_tpo_list: list[str]) -> list[dict]:
    """코디 리스트에 스타일리스트 룰을 적용하여 부적절한 코디 제거.

    TPO가 여러 개면 가장 엄격한 TPO 기준 적용.
    """
    if not user_tpo_list:
        return outfits

    result = []
    for outfit in outfits:
        passed = True
        for tpo in user_tpo_list:
            ok, reason = check_stylist_rules(outfit, tpo)
            if not ok:
                passed = False
                break
        if passed:
            result.append(outfit)

    # 최소 보장: 3개 미만이면 포멀도 기준만 완화하여 재시도
    if len(result) < 3:
        result_relaxed = []
        for outfit in outfits:
            passed = True
            for tpo in user_tpo_list:
                # 금기 카테고리만 체크 (포멀도 완화)
                items = outfit.get("items", [])
                forbidden_cats = TPO_FORBIDDEN_CATEGORIES.get(tpo.lower(), set())
                for item in items:
                    if item.get("category", "") in forbidden_cats:
                        passed = False
                        break
                if not passed:
                    break
            if passed:
                result_relaxed.append(outfit)
        return result_relaxed if len(result_relaxed) >= 3 else outfits[:10]

    return result
```

### feed_builder.py에 통합

stage2_eligibility와 stage3_soft_score 사이에 삽입:

```python
from app.services.stylist_rules import apply_stylist_rules

# feed.py의 get_feed() 수정:
# Stage 2 이후:
eligible = stage2_eligibility(hard_filtered, user_tone_id=tone_id, user_tpo_list=tpo_list)

# NEW: Stylist Rules 적용
styled = apply_stylist_rules(eligible, tpo_list)

# Stage 3에 styled 전달:
scored = stage3_soft_score(styled, ...)
```

### 검증

```bash
cd backend && python -c "
from app.services.stylist_rules import check_stylist_rules
# 면접 + 후드 → 실패
print(check_stylist_rules({'items': [{'category': '후드', 'formality': 2}]}, 'interview'))
# 면접 + 셔츠(f=4) + 슬랙스(f=4) → 통과
print(check_stylist_rules({'items': [{'category': '셔츠', 'formality': 4}, {'category': '슬랙스', 'formality': 4}]}, 'interview'))
"
```

pytest 실행.
```

---

## STEP 5. UI 개선 (P1)

```
### 5-1. 멀티 아이템 이미지 표시

frontend/components/OutfitCard.tsx의 full variant 수정:

1. 메인 이미지 (기존 3:4)는 유지 — items[0] 이미지
2. 메인 이미지 아래에 아이템 리스트 행 추가:
   - 가로 스크롤 가능한 작은 썸네일 리스트
   - 각 아이템: 48x48 rounded-md 썸네일 + 아이템명(truncate 1줄) + 가격
   - 배경: #F0EDE8, gap-2, py-2 px-3
   - 현재 메인 이미지에 표시된 아이템에 Marsala(#964F4C) border-2 강조
3. 썸네일 탭 시:
   - 메인 이미지가 해당 아이템 이미지로 교체 (useState로 관리)
   - 탭한 썸네일에 Marsala 테두리

Props: items 배열은 이미 OutfitCard에 전달되고 있으므로 활용.
compact variant는 변경 없음.

### 5-2. 하단 탭바 4→2 축소

frontend/components/BottomTabBar.tsx 수정:

현재: 홈 / 저장 / Top / 마이 (4탭)
변경: 홈 / 마이 (2탭)

- 저장 탭, Top 탭 제거 (라우트 파일은 유지)
- 홈 → /feed, 마이 → /profile
- 활성: Marsala(#964F4C), 비활성: #8C8578
- 탭바 높이 56px, bg #F8F6F3, 상단 보더 #E5E1DA

### 5-3. evidence/risk_guard 가독성 개선

OutfitCard.tsx full variant 레이아웃 조정:

1. 이미지 max-height: 60vh (3:4 유지하되 화면 비율 제한)
2. core 텍스트를 이미지 하단에 오버레이:
   - 위치: absolute bottom-0, p-3 px-4
   - 배경: linear-gradient(transparent, rgba(0,0,0,0.5))
   - core: white, Nanum Myeongjo 16px, font-bold
   - 가격: white, 15px, font-bold
3. evidence + risk_guard를 이미지 바로 아래:
   - evidence: #8C8578, 13px
   - risk_guard: #6B7F5E, 13px
   - 2줄 이내

### 5-4. core/evidence 텍스트 차별화

backend/app/services/reason_generator.py 수정:

1. core 다양화 (축 1순위에 따라):
   - pcf 1위: "{톤}에 딱 맞는 {TPO} 코디"
   - of 1위: "{TPO}에 최적화된 깔끔한 조합"
   - ch 1위: "색감 조화가 돋보이는 {TPO} 코디"
   - pe 1위: "가성비 좋은 {TPO} 코디"
   - sf 1위: "실루엣이 깔끔한 {TPO} 조합"

2. evidence 다양화: 축별 high/low 각 3변형 = 30패턴
   랜덤 선택 (outfit_id 해시 기반 deterministic)

_build_core()에 scores 파라미터 추가.

### 검증

npm run build 확인.
수정 후 TASK_v3.md 업데이트.
```

---

## STEP 6. QA 레이어 — 사전 출력 검증 (P1)

```
추천 결과가 사용자에게 전달되기 전에 최종 검증하는 QA 게이트를 추가해줘.

파일: backend/app/services/qa_gate.py (신규 생성)

```python
"""
QA Gate — 추천 결과 사전 검증.
feed_builder의 stage4 이후, 응답 직전에 실행.
문제 코디를 제거하고 경고를 로깅한다.
"""

from __future__ import annotations
import logging
from datetime import datetime

logger = logging.getLogger("colorfit.qa")

_MONTH_TO_SEASON = {
    3: "spring", 4: "spring", 5: "spring",
    6: "summer", 7: "summer", 8: "summer",
    9: "autumn", 10: "autumn", 11: "autumn",
    12: "winter", 1: "winter", 2: "winter",
}

_OPPOSITE_SEASONS = {
    "spring": "autumn",
    "summer": "winter",
    "autumn": "spring",
    "winter": "summer",
}


def qa_check(
    outfits: list[dict],
    user_gender: str = "",
    user_tpo_list: list[str] | None = None,
    current_month: int | None = None,
) -> list[dict]:
    """최종 QA 검증. 문제 코디를 제거하고 로그를 남긴다."""
    if current_month is None:
        current_month = datetime.now().month

    current_season = _MONTH_TO_SEASON[current_month]
    opposite = _OPPOSITE_SEASONS[current_season]

    passed = []
    for outfit in outfits:
        issues = []

        # 1. 성별 크로스체크 (최종 방어선)
        if user_gender and user_gender != "unisex":
            for item in outfit.get("items", []):
                ig = item.get("gender", "unisex")
                if ig != "unisex" and ig != user_gender:
                    issues.append(f"gender_mismatch: outfit={user_gender}, item={ig}")

        # 2. 시즌 크로스체크 — 반대 시즌 전용 아이템 감지
        WINTER_KEYWORDS = ["패딩", "롱패딩", "기모", "퍼코트", "무스탕", "울코트", "방한", "털"]
        SUMMER_KEYWORDS = ["민소매", "나시", "슬리브리스", "린넨반팔"]

        if current_season in ("summer", "spring"):
            for item in outfit.get("items", []):
                name = item.get("name", "")
                if any(kw in name for kw in WINTER_KEYWORDS):
                    issues.append(f"season_mismatch: '{name[:20]}' is winter-only")
        elif current_season in ("winter", "autumn"):
            for item in outfit.get("items", []):
                name = item.get("name", "")
                if any(kw in name for kw in SUMMER_KEYWORDS):
                    issues.append(f"season_mismatch: '{name[:20]}' is summer-only")

        # 3. TPO-포멀도 크로스체크
        if user_tpo_list:
            for tpo in user_tpo_list:
                if tpo.lower() == "interview":
                    formalities = [item.get("formality", 3) for item in outfit.get("items", [])]
                    if any(f < 4 for f in formalities):
                        issues.append(f"tpo_formality: interview needs f>=4, got {min(formalities)}")

        if issues:
            oid = outfit.get("outfit_id", "unknown")
            logger.warning(f"QA FAIL [{oid}]: {'; '.join(issues)}")
            continue

        passed.append(outfit)

    removed = len(outfits) - len(passed)
    if removed > 0:
        logger.info(f"QA Gate removed {removed}/{len(outfits)} outfits")

    return passed
```

### feed.py에 통합

```python
from app.services.qa_gate import qa_check

# stage4 이후, 페이지네이션 전:
ranked = stage4_expert_rerank(scored, user_tpo_list=tpo_list)

# NEW: QA Gate
qa_passed = qa_check(ranked, user_gender=gender, user_tpo_list=tpo_list)

total_count = len(qa_passed)
start = (page - 1) * page_size
end = start + page_size
page_outfits = qa_passed[start:end]
```

### 검증

```bash
cd backend && python -c "
from app.services.qa_gate import qa_check

# 4월(봄)에 패딩 코디 → 제거
result = qa_check(
    [{'outfit_id': 'test1', 'items': [{'name': '롱패딩 코트', 'gender': 'female', 'formality': 3}]}],
    user_gender='female',
    current_month=4,
)
print(f'패딩 테스트: {len(result)} (expected: 0)')

# 면접에 포멀도 3 → 제거
result = qa_check(
    [{'outfit_id': 'test2', 'items': [{'name': '셔츠', 'gender': 'female', 'formality': 3}]}],
    user_tpo_list=['interview'],
)
print(f'면접 포멀도 테스트: {len(result)} (expected: 0)')

# 정상 코디 → 통과
result = qa_check(
    [{'outfit_id': 'test3', 'items': [{'name': '셔츠', 'gender': 'female', 'formality': 4}]}],
    user_gender='female',
    user_tpo_list=['interview'],
    current_month=4,
)
print(f'정상 테스트: {len(result)} (expected: 1)')
"
```

pytest 실행.
```

---

## 결과 보고 형식

```
모든 STEP 완료 후 아래 형식으로 보고해줘:

### 한 줄 총평
[이전 문제의 핵심 원인과 해결 방향 1문장]

### 데이터 클렌징 결과
- 시즌 태그 정제: 변경 전 (4시즌 332개, 3시즌 823개) → 변경 후 분포
- 포멀도 기반 TPO 제거: interview에서 N개, commute에서 N개
- 기타 제거: 아동복 N개, 가격이상 N개, 이미지누락 N개
- 최종 코디 수: N개 (원래 1448개)

### 점수 변별력 개선
- 변경 전: total 76.6~81.7 (stdev 0.7)
- 변경 후: total min~max (stdev X.X)
- OF 점수 분포: 100(직접매칭) N개, 85(동의어) N개, 65(그룹) N개, 30(불일치) N개

### 필터링 구조
- Stage 1 (Hard): 성별 + 예산 + 시즌
- Stylist Rules: TPO별 금기카테고리 + 포멀도 + 금기키워드
- Stage 2 (Eligibility): TPO + 브랜드 + 톤 + 스타일
- Stage 3 (Soft Score): 5축 가중합 (OF 30%, SF 25%, PCF 20%, PE 15%, CH 10%)
- Stage 4 (Expert Rerank): 완성코디 가산 + 중복제거
- QA Gate: 성별/시즌/포멀도 최종 검증

### 스타일리스트 룰
- 면접: 금기 12카테고리, 금기 7키워드, 전아이템 포멀도≥4
- 출근: 금기 5카테고리, 금기 3키워드, 평균 포멀도≥3.5

### UI 개선
- 멀티 아이템 썸네일 표시 (48x48, 탭 시 메인 이미지 교체)
- 탭바 4→2 축소
- evidence 가독성: core 오버레이 + evidence 즉시 노출
- core/evidence 텍스트 30패턴 다양화

### QA 체크
- 성별 크로스: N개 차단
- 시즌 크로스: N개 차단 (4월에 겨울 전용 아이템)
- TPO-포멀도 크로스: N개 차단

### 개선 전/후 비교 (각 스크린샷 케이스)
1. 출근 민트가디건 → [개선 후 예상 결과]
2. 여성에 남성바지 → [QA Gate에서 차단됨]
3. 비슷한 선택 갭 → [앵커 유사도 기반으로 같은 TPO/시즌 코디 표시]
4. 4월 겨울패딩 → [시즌태그 정제 + QA Gate 이중 차단]
5. 면접 벨벳드레스 → [스타일리스트 룰에서 차단 (벨벳 키워드)]
```

---

## 실행 체크리스트

```
□ STEP 0: feed.py + feed_builder.py 파일 복원, import 검증 통과
□ STEP 1: 시즌태그 정제 + 포멀도 검증 + 데이터 클렌징 완료
□ STEP 2: 점수 변별력 확보 (stdev ≥ 3.0 확인)
□ STEP 3: 비슷한 선택 앵커 기반으로 변경 + build 성공
□ STEP 4: 스타일리스트 룰 적용 + pytest 통과
□ STEP 5: UI 개선 4건 + build 성공
□ STEP 6: QA Gate 적용 + 검증 테스트 통과
□ 결과 보고서 작성
```
