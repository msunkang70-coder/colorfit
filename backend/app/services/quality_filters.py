"""
품질 필터 시스템 — 추천 품질을 보장하는 3단계 방어 체계.

1. Category Filter: 비의류 아이템 제거
2. Brand Tier Filter: TPO별 브랜드 등급 매칭
3. Age Fit Filter: 연령 부적합 키워드 제거

feed_builder의 stage2_eligibility 이후, stylist_rules 이전에 적용.
"""

from __future__ import annotations

# ──────────────────────────────────────────────
# 1. Category Filter — 비의류 아이템 감지
# ──────────────────────────────────────────────

# 비의류 키워드 (상품명에 포함 시 해당 아이템은 의류가 아님)
NON_CLOTHING_KEYWORDS = [
    "침대", "매트리스", "이불", "베개", "커튼", "카펫", "러그",
    "가구", "수납", "선반", "조명", "인테리어",
    "식기", "컵", "접시", "주방",
    "화장품", "향수", "립스틱",
    "폰케이스", "충전기", "이어폰",
    "완구", "장난감", "인형",
    "반려동물", "사료", "강아지",
]


def has_non_clothing_item(outfit: dict) -> bool:
    """코디에 비의류 아이템이 포함되어 있는지."""
    for item in outfit.get("items", []):
        name = item.get("name", "").lower()
        for kw in NON_CLOTHING_KEYWORDS:
            if kw in name:
                return True
    return False


# ──────────────────────────────────────────────
# 2. Brand Tier Filter — 브랜드 등급 분류
# ──────────────────────────────────────────────

# 브랜드 등급 (이름 일부 매칭)
SPORT_BRANDS = [
    "아디다스", "adidas", "나이키", "nike", "퓨마", "puma",
    "안다르", "andar", "젝시믹스", "xexymix",
    "뉴발란스", "new balance", "언더아머", "under armour",
    "리복", "reebok", "디스커스", "discus",
    "내셔널지오그래픽", "national geographic",
    "노스페이스", "north face", "컬럼비아", "columbia",
    "파타고니아", "patagonia",
]

CASUAL_BRANDS = [
    "유니클로", "uniqlo", "h&m", "에이치앤엠",
    "자라", "zara", "스파오", "spao",
    "탑텐", "topten", "무신사 스탠다드",
    "에잇세컨즈", "8seconds",
]

FORMAL_BRANDS = [
    "코스", "cos", "마시모두띠", "massimo dutti",
    "빈폴", "beanpole", "헤지스", "hazzys",
    "타미힐피거", "tommy hilfiger",
    "폴햄", "폴로", "polo", "잇미샤",
    "리스트", "list", "지오다노",
]

# TPO별 금지 브랜드 등급
TPO_BRAND_BLACKLIST: dict[str, list[str]] = {
    "interview": SPORT_BRANDS,
    "commute": SPORT_BRANDS[:10],  # 주요 스포츠 브랜드만
    "event": SPORT_BRANDS,
    "date": [],
    "campus": [],
    "weekend": [],
    "travel": [],
    "workout": FORMAL_BRANDS,
}


def has_blacklisted_brand(outfit: dict, tpo: str) -> bool:
    """코디에 해당 TPO에서 금지된 브랜드가 포함되어 있는지."""
    blacklist = TPO_BRAND_BLACKLIST.get(tpo.lower(), [])
    if not blacklist:
        return False

    for item in outfit.get("items", []):
        name = item.get("name", "").lower()
        brand = item.get("brand", "").lower()
        mall = item.get("mall_name", "").lower()
        combined = f"{name} {brand} {mall}"
        for bl in blacklist:
            if bl.lower() in combined:
                return True
    return False


# ──────────────────────────────────────────────
# 3. Age Fit Filter — 연령 부적합 키워드
# ──────────────────────────────────────────────

# 상품명에 포함 시 젊은 사용자에게 부적합
OLD_TARGET_KEYWORDS = [
    "엄마", "할머니", "중년", "노년", "시니어", "50대", "60대",
    "어르신", "효도", "부모님",
]

# 상품명에 포함 시 성인에게 부적합
KIDS_TARGET_KEYWORDS = [
    "키즈", "아동", "유아", "주니어", "kids", "baby", "베이비",
]


def has_age_mismatch_keyword(outfit: dict) -> bool:
    """코디에 연령 부적합 키워드가 포함되어 있는지."""
    for item in outfit.get("items", []):
        name = item.get("name", "").lower()
        for kw in OLD_TARGET_KEYWORDS + KIDS_TARGET_KEYWORDS:
            if kw in name:
                return True
    return False


# ──────────────────────────────────────────────
# 통합 필터 함수
# ──────────────────────────────────────────────

def apply_quality_filters(
    outfits: list[dict],
    user_tpo_list: list[str] | None = None,
) -> list[dict]:
    """3단계 품질 필터를 순차 적용.

    Returns:
        필터 통과한 코디 리스트
    """
    if user_tpo_list is None:
        user_tpo_list = []

    result = []
    for outfit in outfits:
        # 1. 비의류 필터
        if has_non_clothing_item(outfit):
            continue

        # 2. 브랜드 등급 필터
        blocked = False
        for tpo in user_tpo_list:
            if has_blacklisted_brand(outfit, tpo):
                blocked = True
                break
        if blocked:
            continue

        # 3. 연령 키워드 필터
        if has_age_mismatch_keyword(outfit):
            continue

        result.append(outfit)

    return result
