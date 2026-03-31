"""
피드 빌더 — Hard Filter 체인 + Soft Score + 리랭킹.
기획서 섹션 5.4 (Hard Filter), 6.1 (파이프라인) 참조.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from app.services.scoring import TONE_COMPAT, TPO_SYNONYMS
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
