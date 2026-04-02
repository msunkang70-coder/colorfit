"""
스타일리스트 룰 — TPO별 아이템 제약 조건.
stage2_eligibility 이후, stage3_soft_score 이전에 적용.
"""

from __future__ import annotations

TPO_FORBIDDEN_CATEGORIES: dict[str, set[str]] = {
    "interview": {
        "크롭탑", "민소매", "숏팬츠", "반바지", "후드", "맨투맨",
        "레깅스", "샌들", "슬리퍼", "스니커즈", "패딩", "점퍼",
    },
    "commute": {
        "크롭탑", "숏팬츠", "반바지", "슬리퍼", "레깅스", "패딩",
    },
    "event": {"후드", "맨투맨", "슬리퍼"},
    "date": {"슬리퍼"},
}

TPO_MIN_FORMALITY: dict[str, float] = {
    "interview": 4.0,
    "commute": 3.5,
    "event": 3.5,
    "date": 3.0,
    "campus": 2.0,
    "weekend": 2.0,
    "travel": 2.0,
    "workout": 1.0,
}

TPO_FORBIDDEN_KEYWORDS: dict[str, list[str]] = {
    "interview": ["벨벳", "시스루", "크롭", "오버사이즈", "빈티지", "찢어진", "디스트로이드"],
    "commute": ["시스루", "크롭", "찢어진"],
}


def check_stylist_rules(outfit: dict, tpo: str) -> tuple[bool, str]:
    """코디가 해당 TPO의 스타일리스트 룰을 통과하는지 검사."""
    items = outfit.get("items", [])
    if not items:
        return False, "아이템 없음"

    tpo_lower = tpo.lower()

    # 1. 금기 카테고리
    forbidden_cats = TPO_FORBIDDEN_CATEGORIES.get(tpo_lower, set())
    for item in items:
        cat = item.get("category", "")
        if cat in forbidden_cats:
            return False, f"{tpo}에 부적절한 카테고리: {cat}"

    # 2. 포멀도
    min_formality = TPO_MIN_FORMALITY.get(tpo_lower, 2.0)
    formalities = [item.get("formality", 3) for item in items]

    if tpo_lower == "interview":
        if any(f < min_formality for f in formalities):
            return False, f"면접 포멀도 미달: {min(formalities)}"
    else:
        avg = sum(formalities) / len(formalities)
        if avg < min_formality:
            return False, f"{tpo} 평균 포멀도 {avg:.1f} < {min_formality}"

    # 3. 금기 키워드
    forbidden_kw = TPO_FORBIDDEN_KEYWORDS.get(tpo_lower, [])
    for item in items:
        name = item.get("name", "")
        for kw in forbidden_kw:
            if kw in name:
                return False, f"{tpo}에 부적절: '{kw}'"

    return True, ""


def apply_stylist_rules(outfits: list[dict], user_tpo_list: list[str]) -> list[dict]:
    """코디 리스트에 스타일리스트 룰을 적용."""
    if not user_tpo_list:
        return outfits

    result = []
    for outfit in outfits:
        passed = True
        for tpo in user_tpo_list:
            ok, _ = check_stylist_rules(outfit, tpo)
            if not ok:
                passed = False
                break
        if passed:
            result.append(outfit)

    # 최소 보장: 3개 미만이면 카테고리만 체크 (포멀도 완화)
    if len(result) < 3:
        relaxed = []
        for outfit in outfits:
            passed = True
            for tpo in user_tpo_list:
                forbidden_cats = TPO_FORBIDDEN_CATEGORIES.get(tpo.lower(), set())
                for item in outfit.get("items", []):
                    if item.get("category", "") in forbidden_cats:
                        passed = False
                        break
                if not passed:
                    break
            if passed:
                relaxed.append(outfit)
        return relaxed if len(relaxed) >= 3 else outfits[:10]

    return result
