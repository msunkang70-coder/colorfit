"""
StyleFilter — 규칙 기반 스타일 호환성 사전 필터.
카테고리 궁합(50%) + 실루엣 밸런스(25%) + 포멀도 일관성(25%) 합산
55점 미만 코디를 피드에서 사전 제거한다.
기획서 섹션 6.6, H8 참조.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

# classifier.py는 scripts/ 하에 있으므로 경로 추가
_SCRIPTS_DIR = str(Path(__file__).resolve().parents[2] / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from classifier import classify_by_keyword, lookup_cache
from app.services.scoring import calculate_sf

# SF 컷오프 점수 (기획서: 55점 미만 제거)
SF_CUTOFF = 55.0


def detect_category(
    title: str,
    category3: str = "",
    product_id: Optional[str] = None,
) -> dict[str, Any]:
    """아이템의 카테고리·실루엣·포멀도를 감지한다.

    3단계 폴백: 키워드 → LLM 캐시 → 기본값
    (런타임에서는 Gemini 호출하지 않음, 배치에서 사전 분류)

    Args:
        title: 상품명
        category3: 네이버 카테고리3 힌트
        product_id: LLM 캐시 조회용 상품 ID

    Returns:
        {"category", "silhouette", "formality"} 딕셔너리
    """
    # 1단계: 키워드 매칭
    result = classify_by_keyword(title, category3)
    if result:
        return {
            "category": result["category"],
            "silhouette": result.get("silhouette", "regular"),
            "formality": result.get("formality", 3),
        }

    # 2단계: LLM 캐시
    if product_id:
        cached = lookup_cache(product_id)
        if cached:
            return {
                "category": cached["category"],
                "silhouette": cached.get("silhouette", "regular"),
                "formality": cached.get("formality", 3),
            }

    # 3단계: 기본값 (미분류)
    return {
        "category": "unknown",
        "silhouette": "regular",
        "formality": 3,
    }


def _classify_items(items: list[dict]) -> tuple[list[str], Optional[str], Optional[str]]:
    """아이템 리스트에서 카테고리, 상의/하의 실루엣을 추출한다."""
    categories: list[str] = []
    top_silhouette: Optional[str] = None
    bottom_silhouette: Optional[str] = None

    _TOP_CATEGORIES = {
        "니트", "셔츠", "블라우스", "티셔츠", "맨투맨", "후드",
        "크롭탑", "반팔", "머슬핏", "탱크탑",
        "knit", "shirt", "blouse", "tshirt", "sweatshirt", "hoodie",
        "crop_top", "vest",
    }
    _BOTTOM_CATEGORIES = {
        "슬랙스", "청바지", "스커트", "와이드팬츠", "레깅스",
        "숏팬츠", "조거팬츠", "치노",
        "slacks", "jeans", "skirt", "wide_pants", "leggings",
        "shorts", "jogger", "chino", "mini_skirt", "high_waist_pants",
    }

    # 카테고리 → 영문 매핑 (scoring.py의 style_compat.json 키 호환)
    _KO_TO_EN: dict[str, str] = {
        "니트": "knit", "셔츠": "shirt", "블라우스": "blouse",
        "티셔츠": "tshirt", "맨투맨": "sweatshirt", "후드": "hoodie",
        "크롭탑": "crop_top", "반팔": "tshirt", "머슬핏": "tshirt",
        "탱크탑": "tshirt",
        "슬랙스": "slacks", "청바지": "jeans", "스커트": "skirt",
        "와이드팬츠": "wide_pants", "레깅스": "leggings",
        "숏팬츠": "shorts", "조거팬츠": "jogger", "치노": "chino",
        "자켓": "jacket", "코트": "coat", "패딩": "padding",
        "가디건": "cardigan", "점퍼": "jacket",
        "원피스": "onepiece",
        "로퍼": "loafer", "스니커즈": "sneakers", "힐": "heels",
        "부츠": "boots", "샌들": "sandals",
        "토트백": "bag_tote", "크로스백": "bag_cross",
    }

    for item in items:
        title = item.get("title", item.get("name", ""))
        cat3 = item.get("category3", "")
        pid = item.get("product_id")

        detected = detect_category(title, cat3, pid)
        cat = detected["category"]
        sil = detected["silhouette"]

        # 영문 변환
        cat_en = _KO_TO_EN.get(cat, cat)
        categories.append(cat_en)

        # 실루엣 추출
        if cat in _TOP_CATEGORIES or cat_en in _TOP_CATEGORIES:
            if not top_silhouette:
                top_silhouette = sil
        elif cat in _BOTTOM_CATEGORIES or cat_en in _BOTTOM_CATEGORIES:
            if not bottom_silhouette:
                bottom_silhouette = sil

    return categories, top_silhouette, bottom_silhouette


def filter_outfit(items: list[dict]) -> tuple[bool, float, dict]:
    """코디의 StyleFilter 통과 여부를 판단한다.

    Args:
        items: 코디 아이템 리스트 (각 아이템은 title/name, category3, product_id 포함)

    Returns:
        (passed, sf_score, details) 튜플
        - passed: 55점 이상이면 True
        - sf_score: SF 점수 (0~100)
        - details: 카테고리, 실루엣 등 상세 정보
    """
    categories, top_sil, bottom_sil = _classify_items(items)

    sf_score = calculate_sf(categories, top_sil, bottom_sil)

    details = {
        "categories_detected": categories,
        "top_silhouette": top_sil,
        "bottom_silhouette": bottom_sil,
        "sf_score": sf_score,
    }

    return sf_score >= SF_CUTOFF, sf_score, details
