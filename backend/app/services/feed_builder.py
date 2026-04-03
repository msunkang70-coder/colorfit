"""
피드 빌더 — Hard Filter 체인 + Soft Score + 리랭킹.
기획서 섹션 5.4 (Hard Filter), 6.1 (파이프라인) 참조.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from app.services.scoring import (
    TONE_COMPAT, TPO_SYNONYMS,
    calculate_pcf, calculate_of, calculate_ch, calculate_pe, calculate_sf,
)
from app.services.style_filter import filter_outfit

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_BRAND_WL_PATH = _DATA_DIR / "brand_whitelist.json"

_brand_whitelist: set[str] | None = None


def _load_brand_whitelist() -> set[str]:
    global _brand_whitelist
    if _brand_whitelist is not None:
        return _brand_whitelist
    with open(_BRAND_WL_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    brands = data if isinstance(data, list) else data.get("brands", [])
    _brand_whitelist = {b.lower() for b in brands if isinstance(b, str)}
    return _brand_whitelist


# ──────────────────────────────────────────────
# 시즌 매핑 (기획서 H3)
# ──────────────────────────────────────────────
_MONTH_TO_SEASON: dict[int, str] = {
    3: "spring", 4: "spring", 5: "spring",
    6: "summer", 7: "summer", 8: "summer",
    9: "autumn", 10: "autumn", 11: "autumn",
    12: "winter", 1: "winter", 2: "winter",
}

_ADJACENT_SEASONS: dict[str, set[str]] = {
    "spring": {"spring", "summer", "winter"},
    "summer": {"summer", "spring", "autumn"},
    "autumn": {"autumn", "summer", "winter"},
    "winter": {"winter", "autumn", "spring"},
}

# 호환 톤: 동일 시즌 + 같은 온도 계열 (TONE_COMPAT에서 60점 이상)
def _get_compatible_tones(user_tone_id: str) -> set[str]:
    """사용자 톤과 호환되는 톤 집합 (H7용, 60점 이상)."""
    compat = TONE_COMPAT.get(user_tone_id, {})
    return {t for t, score in compat.items() if score >= 60}


# ──────────────────────────────────────────────
# Hard Filter 개별 함수
# ──────────────────────────────────────────────

def filter_h1_gender(outfit: dict, user_gender: str) -> bool:
    """H1. 성별 불일치 필터.
    코디 내 아이템 중 하나라도 반대 성별이면 제거.
    """
    if not user_gender or user_gender == "unisex":
        return True

    for item in outfit.get("items", []):
        item_gender = item.get("gender", "unisex")
        if item_gender == "unisex" or item_gender == user_gender:
            continue
        return False
    return True


def filter_h2_budget(outfit: dict, budget_max: float) -> bool:
    """H2. 예산 초과 필터. 코디 총액 > budget_max × 1.5 이면 제거."""
    if budget_max <= 0:
        return True
    total_price = outfit.get("total_price", 0)
    return total_price <= budget_max * 1.5


def filter_h3_season(outfit: dict, current_month: Optional[int] = None) -> bool:
    """H3. 계절 완전 불일치 필터.
    현재 시즌과 완전 반대 시즌이면 제거. 인접 시즌은 허용.
    TPO가 travel이면 필터 완화.
    """
    if current_month is None:
        current_month = datetime.now().month

    current_season = _MONTH_TO_SEASON[current_month]
    allowed = _ADJACENT_SEASONS[current_season]

    tags = outfit.get("tags", [])

    # TPO에 travel 있으면 시즌 필터 완화
    if "travel" in tags:
        return True

    # 코디에 시즌 태그가 있는지 확인
    outfit_seasons = {t for t in tags if t in {"spring", "summer", "autumn", "winter"}}
    if not outfit_seasons:
        return True  # 시즌 태그 없으면 통과

    # 하나라도 허용 시즌에 속하면 통과
    return bool(outfit_seasons & allowed)


def filter_h4_tpo(outfit: dict, user_tpo_list: list[str]) -> bool:
    """H4. TPO 완전 불일치 필터.
    동의어 확장 후에도 매칭 0이면 제거.
    """
    if not user_tpo_list:
        return True

    # 사용자 TPO 동의어 확장
    expanded: set[str] = set()
    for tpo in user_tpo_list:
        tpo_lower = tpo.lower()
        expanded.update(TPO_SYNONYMS.get(tpo_lower, {tpo_lower}))

    outfit_tpo = {t.lower() for t in outfit.get("designed_tpo", outfit.get("tags", []))}

    return bool(outfit_tpo & expanded)


def filter_h5_brand(outfit: dict) -> bool:
    """H5. 브랜드 화이트리스트 필터.
    코디 내 아이템 중 1개 이상이 화이트리스트 브랜드면 통과.
    """
    whitelist = _load_brand_whitelist()
    for item in outfit.get("items", []):
        brand = item.get("brand", item.get("mall_name", "")).lower()
        if brand in whitelist:
            return True
    return False


def filter_h6_llm_quality(outfit: dict) -> bool:
    """H6. LLM 품질 필터. 3점 미만 제거.
    프리컴퓨팅된 llm_quality_score 사용.
    """
    score = outfit.get("llm_quality_score", 5)  # 미평가 시 통과
    return score >= 3


def filter_h7_tone(outfit: dict, user_tone_id: str) -> bool:
    """H7. 톤 호환성 필터 (P1 우선 원칙).
    사용자 톤 + 호환 톤에 매칭되는 아이템이 0개이면 제거.
    """
    if not user_tone_id:
        return True

    compatible = _get_compatible_tones(user_tone_id)
    compatible.add(user_tone_id)

    for item in outfit.get("items", []):
        item_tone = item.get("tone_id")
        if item_tone and item_tone in compatible:
            return True

    # tone_id가 없는 아이템만 있으면 통과 (톤 정보 불완전)
    has_any_tone = any(item.get("tone_id") for item in outfit.get("items", []))
    return not has_any_tone


def filter_h8_style(outfit: dict) -> tuple[bool, float, dict]:
    """H8. StyleFilter 컷오프. 55점 미만 제거."""
    return filter_outfit(outfit.get("items", []))


# ──────────────────────────────────────────────
# Hard Filter 체인
# ──────────────────────────────────────────────

def apply_hard_filters(
    outfits: list[dict],
    user_gender: str = "",
    budget_max: float = 0,
    user_tpo_list: list[str] | None = None,
    user_tone_id: str = "",
    current_month: int | None = None,
) -> list[dict]:
    """Hard Filter 8단계를 순차 적용한다.

    적용 순서 (비용 낮은 순):
    H1 성별 → H2 예산 → H3 계절 → H4 TPO → H5 브랜드 → H7 톤 → H8 StyleFilter → H6 LLM

    Args:
        outfits: 코디 리스트
        user_gender: 사용자 성별 (female/male/unisex)
        budget_max: 예산 상한
        user_tpo_list: 사용자 TPO 리스트
        user_tone_id: 사용자 톤 ID
        current_month: 현재 월 (테스트용, None이면 자동)

    Returns:
        Hard Filter 통과한 코디 리스트 (각 코디에 style_details 추가)
    """
    if user_tpo_list is None:
        user_tpo_list = []

    passed: list[dict] = []

    for outfit in outfits:
        # H1: 성별
        if not filter_h1_gender(outfit, user_gender):
            continue

        # H2: 예산
        if not filter_h2_budget(outfit, budget_max):
            continue

        # H3: 계절
        if not filter_h3_season(outfit, current_month):
            continue

        # H4: TPO
        if user_tpo_list and not filter_h4_tpo(outfit, user_tpo_list):
            continue

        # H5: 브랜드
        if not filter_h5_brand(outfit):
            continue

        # H7: 톤
        if not filter_h7_tone(outfit, user_tone_id):
            continue

        # H8: StyleFilter
        style_passed, sf_score, style_details = filter_h8_style(outfit)
        if not style_passed:
            continue

        # H6: LLM 품질
        if not filter_h6_llm_quality(outfit):
            continue

        outfit["style_details"] = style_details
        passed.append(outfit)

    return passed


# ──────────────────────────────────────────────
# 4단계 파이프라인 (리팩토링)
# ──────────────────────────────────────────────

def stage1_hard_filter(
    outfits: list[dict],
    user_gender: str = "",
    budget_max: float = 0,
    current_month: int | None = None,
) -> list[dict]:
    """Stage 1: 객관적 불일치 즉시 제거 (H1 성별, H2 예산, H3 계절)."""
    passed = []
    for outfit in outfits:
        if not filter_h1_gender(outfit, user_gender):
            continue
        if not filter_h2_budget(outfit, budget_max):
            continue
        if not filter_h3_season(outfit, current_month):
            continue
        passed.append(outfit)
    return passed


def stage2_eligibility(
    outfits: list[dict],
    user_tone_id: str = "",
    user_tpo_list: list[str] | None = None,
    disliked_ids: set[str] | None = None,
) -> list[dict]:
    """Stage 2: 적합성 게이트 (H4 TPO, H5 브랜드, H6 LLM, H7 톤, H8 Style).
    최소 보장: 5개 미만이면 톤/TPO 기준 완화하여 재시도."""
    if user_tpo_list is None:
        user_tpo_list = []
    if disliked_ids is None:
        disliked_ids = set()

    def _filter(tone_check: bool, tpo_check: bool) -> list[dict]:
        passed = []
        for outfit in outfits:
            oid = outfit.get("outfit_id", "")
            if oid in disliked_ids:
                continue
            if tpo_check and user_tpo_list and not filter_h4_tpo(outfit, user_tpo_list):
                continue
            if not filter_h5_brand(outfit):
                continue
            if tone_check and not filter_h7_tone(outfit, user_tone_id):
                continue
            style_passed, sf_score, style_details = filter_h8_style(outfit)
            if not style_passed:
                continue
            if not filter_h6_llm_quality(outfit):
                continue
            outfit["style_details"] = style_details
            passed.append(outfit)
        return passed

    # 정상 필터링
    result = _filter(tone_check=True, tpo_check=True)
    if len(result) >= 5:
        return result

    # 톤 완화
    result = _filter(tone_check=False, tpo_check=True)
    if len(result) >= 5:
        return result

    # TPO도 완화
    result = _filter(tone_check=False, tpo_check=False)
    return result


def stage3_soft_score(
    outfits: list[dict],
    user_tone_id: str = "",
    user_tpo_list: list[str] | None = None,
    budget_min: float = 0,
    budget_max: float = 300000,
    weight_overrides: dict[str, float] | None = None,
) -> list[dict]:
    """Stage 3: Soft Score 계산 + 총점순 정렬. 제거 금지."""
    if user_tpo_list is None:
        user_tpo_list = []

    _adjust_weights_by_data_quality(outfits)

    for outfit in outfits:
        scores = compute_soft_scores(
            outfit, user_tone_id, user_tpo_list,
            budget_min, budget_max, weight_overrides,
        )
        outfit["scores"] = scores

    outfits.sort(key=lambda o: o.get("scores", {}).get("total", 0), reverse=True)
    return outfits


# TPO별 대표 스타일 (순서 = 우선순위)
TPO_REPRESENTATIVE_STYLES: dict[str, list[str]] = {
    "interview": ["formal", "minimal"],
    "commute": ["minimal", "formal"],
    "date": ["feminine", "minimal", "casual"],
    "campus": ["casual", "sporty", "minimal"],
    "weekend": ["casual", "minimal"],
    "travel": ["casual", "sporty"],
    "event": ["formal", "feminine"],
    "workout": ["sporty"],
}


def stage4_expert_rerank(
    outfits: list[dict],
    user_tpo_list: list[str] | None = None,
    preferences: dict | None = None,
    max_results: int = 200,
) -> list[dict]:
    """Stage 4: Expert Rerank — TPO 대표 스타일 보너스 + 완성 코디 가산 + 중복 제거."""
    if user_tpo_list is None:
        user_tpo_list = []

    # TPO 대표 스타일 보너스
    tpo_key = user_tpo_list[0].lower() if user_tpo_list else ""
    rep_styles = TPO_REPRESENTATIVE_STYLES.get(tpo_key, [])

    for outfit in outfits:
        scores = outfit.get("scores", {})
        style = outfit.get("style_tag", "")
        bonus = 0.0

        # 대표 스타일 보너스 (1순위 +12, 2순위 +5, 3순위 +2)
        if style and rep_styles:
            if style == rep_styles[0]:
                bonus += 12.0
            elif len(rep_styles) > 1 and style == rep_styles[1]:
                bonus += 5.0
            elif len(rep_styles) > 2 and style == rep_styles[2]:
                bonus += 2.0

        # 품질 점수 보너스
        quality = outfit.get("quality_score", 0)
        if quality >= 70:
            bonus += 3.0

        scores["style_bonus"] = bonus
        outfit["scores"] = scores

    return rerank(outfits, preferences=preferences, max_results=max_results)


# ──────────────────────────────────────────────
# 5축 기본 가중치 (기획서 5.5)
# ──────────────────────────────────────────────
DEFAULT_WEIGHTS = {
    "pcf": 0.20,
    "of": 0.30,
    "ch": 0.10,
    "pe": 0.15,
    "sf": 0.25,
}


# ──────────────────────────────────────────────
# 데이터 품질 기반 가중치 동적 조정
# ──────────────────────────────────────────────

_effective_weights: dict[str, float] | None = None


def _adjust_weights_by_data_quality(outfits_sample: list[dict]) -> dict[str, float]:
    """color_hex 데이터 품질을 검사하여 CH 가중치를 동적 조정."""
    global _effective_weights
    if _effective_weights is not None:
        return _effective_weights

    # 샘플 10개의 color_hex 검사
    empty_count = 0
    total_checked = 0
    for o in outfits_sample[:10]:
        for it in o.get("items", []):
            total_checked += 1
            hex_val = it.get("color_hex", "")
            if not hex_val or hex_val == "" or hex_val == "#808080":
                empty_count += 1

    # 80% 이상 비어있으면 CH 가중치 0
    w = dict(DEFAULT_WEIGHTS)
    if total_checked > 0 and empty_count / total_checked >= 0.8:
        w["ch"] = 0.0
        # 나머지 정규화
        remaining = sum(v for k, v in w.items() if k != "ch")
        if remaining > 0:
            for k in w:
                if k != "ch":
                    w[k] = w[k] / remaining

    _effective_weights = w
    return _effective_weights


# ──────────────────────────────────────────────
# Soft Score 계산
# ──────────────────────────────────────────────

def compute_soft_scores(
    outfit: dict,
    user_tone_id: str,
    user_tpo_list: list[str],
    budget_min: float,
    budget_max: float,
    weight_overrides: dict[str, float] | None = None,
) -> dict:
    """코디에 5축 스코어를 계산하여 부착한다.

    Args:
        outfit: 코디 딕셔너리 (items 포함)
        user_tone_id: 사용자 톤 ID
        user_tpo_list: 사용자 TPO 리스트
        budget_min / budget_max: 예산 범위
        weight_overrides: 개인화 가중치 오버라이드

    Returns:
        scores 딕셔너리 (pcf, of, ch, pe, sf, total)
    """
    items = outfit.get("items", [])

    # PCF
    item_tone_ids = [it.get("tone_id") for it in items]
    item_hex_colors = [it.get("color_hex", "#808080") for it in items]
    pcf = calculate_pcf(item_tone_ids, item_hex_colors, user_tone_id)

    # OF
    outfit_tags = outfit.get("designed_tpo", outfit.get("tags", []))
    of = calculate_of(outfit_tags, user_tpo_list)

    # CH
    ch = calculate_ch(item_hex_colors)

    # PE
    total_price = outfit.get("total_price", 0)
    pe = calculate_pe(total_price, budget_min, budget_max)

    # SF — 프리컴퓨팅된 style_details 활용 또는 새로 계산
    style_details = outfit.get("style_details", {})
    sf = style_details.get("sf_score")
    if sf is None:
        categories = [it.get("category", "unknown") for it in items]
        sf = calculate_sf(categories)

    # 가중합 — 데이터 품질 기반 effective weights 사용
    w = dict(_effective_weights or DEFAULT_WEIGHTS)
    if weight_overrides:
        for k, v in weight_overrides.items():
            if k in w:
                w[k] = v
        # 정규화
        total_w = sum(w.values())
        if total_w > 0:
            w = {k: v / total_w for k, v in w.items()}

    total = (
        pcf * w["pcf"]
        + of * w["of"]
        + ch * w["ch"]
        + pe * w["pe"]
        + sf * w["sf"]
    )

    scores = {
        "pcf": round(pcf, 2),
        "of": round(of, 2),
        "ch": round(ch, 2),
        "pe": round(pe, 2),
        "sf": round(sf, 2),
        "total": round(total, 2),
    }
    return scores


# ──────────────────────────────────────────────
# 개인화 보정 (-10 ~ +10)
# ──────────────────────────────────────────────

def _personalization_bonus(
    outfit: dict,
    preferences: dict | None,
) -> float:
    """사용자 선호 톤/카테고리/브랜드 일치에 따른 보정 점수."""
    if not preferences:
        return 0.0

    bonus = 0.0

    # 톤 선호
    preferred_tones = preferences.get("tone_preferences", {})
    for item in outfit.get("items", []):
        tone = item.get("tone_id", "")
        if tone in preferred_tones:
            bonus += min(preferred_tones[tone], 3.0)

    # 카테고리 선호
    preferred_cats = preferences.get("category_preferences", {})
    for item in outfit.get("items", []):
        cat = item.get("category", "")
        if cat in preferred_cats:
            bonus += min(preferred_cats[cat], 2.0)

    # 브랜드 선호
    preferred_brands = preferences.get("brand_preferences", {})
    for item in outfit.get("items", []):
        brand = item.get("brand", "").lower()
        if brand in preferred_brands:
            bonus += min(preferred_brands[brand], 2.0)

    return max(-10.0, min(10.0, bonus))


# ──────────────────────────────────────────────
# 리랭킹
# ──────────────────────────────────────────────

def rerank(
    outfits: list[dict],
    disliked_ids: set[str] | None = None,
    preferences: dict | None = None,
    max_results: int = 200,
) -> list[dict]:
    """Soft Score 기반 리랭킹.

    기획서 6.1 5단계:
    - 완성 코디 가산 (+3점)
    - dislike 제외
    - 톤 다양성 (동일 톤 3개 제한)
    - 메인아이템 중복 제거 (1개 제한)
    - 개인화 보정 (-10 ~ +10)

    Returns:
        리랭킹된 코디 리스트 (상위 max_results개)
    """
    if disliked_ids is None:
        disliked_ids = set()

    # 1. dislike 제외
    candidates = [
        o for o in outfits
        if o.get("outfit_id", "") not in disliked_ids
    ]

    # 2. 점수 보정
    for outfit in candidates:
        scores = outfit.get("scores", {})
        total = scores.get("total", 0.0)

        # 완성 코디 가산: 상의+하의+아우터 있으면 +3점
        if outfit.get("is_complete_outfit", False):
            total += 3.0

        # 개인화 보정
        total += _personalization_bonus(outfit, preferences)

        # TPO 대표 스타일 보너스
        total += scores.get("style_bonus", 0.0)

        scores["reranked_total"] = round(min(total, 100.0), 2)
        outfit["scores"] = scores

    # 3. 총점 기준 내림차순 정렬
    candidates.sort(key=lambda o: o.get("scores", {}).get("reranked_total", 0), reverse=True)

    # 4. 다양성 보장: 톤 다양성 + 메인아이템 중복 제거
    result: list[dict] = []
    tone_counts: dict[str, int] = {}
    main_item_ids: set[str] = set()

    for outfit in candidates:
        if len(result) >= max_results:
            break

        # 톤 다양성: 코디의 대표 톤 기준 동일 톤 3개 제한
        dominant_tone = _get_dominant_tone(outfit)
        if dominant_tone:
            count = tone_counts.get(dominant_tone, 0)
            if count >= 3:
                continue
            tone_counts[dominant_tone] = count + 1

        # 메인아이템 중복 제거: 동일 메인 아이템 1개 제한
        main_id = _get_main_item_id(outfit)
        if main_id:
            if main_id in main_item_ids:
                continue
            main_item_ids.add(main_id)

        result.append(outfit)

    return result


def _get_dominant_tone(outfit: dict) -> str | None:
    """코디의 대표 톤 (가장 많이 등장하는 톤)."""
    tones: dict[str, int] = {}
    for item in outfit.get("items", []):
        tone = item.get("tone_id")
        if tone:
            tones[tone] = tones.get(tone, 0) + 1
    if not tones:
        return None
    return max(tones, key=tones.get)


def _get_main_item_id(outfit: dict) -> str | None:
    """코디의 메인 아이템 ID (첫 번째 아이템)."""
    items = outfit.get("items", [])
    if items:
        return items[0].get("product_id")
    return None


# ──────────────────────────────────────────────
# 전체 Soft Score + 리랭킹 파이프라인
# ──────────────────────────────────────────────

def score_and_rerank(
    outfits: list[dict],
    user_tone_id: str,
    user_tpo_list: list[str],
    budget_min: float,
    budget_max: float,
    weight_overrides: dict[str, float] | None = None,
    disliked_ids: set[str] | None = None,
    preferences: dict | None = None,
    max_results: int = 200,
) -> list[dict]:
    """Hard Filter 통과 코디에 Soft Score 계산 + 리랭킹.

    Returns:
        스코어링 + 리랭킹된 상위 max_results개 코디 리스트
    """
    # 데이터 품질 기반 가중치 조정 (한 번만)
    _adjust_weights_by_data_quality(outfits)

    # 4단계: Scoring
    for outfit in outfits:
        scores = compute_soft_scores(
            outfit, user_tone_id, user_tpo_list,
            budget_min, budget_max, weight_overrides,
        )
        outfit["scores"] = scores

    # 5단계: Re-ranking
    return rerank(outfits, disliked_ids, preferences, max_results)
