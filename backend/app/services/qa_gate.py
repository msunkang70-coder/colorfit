"""
QA Gate — 추천 결과 사전 검증.
stage4 이후, 응답 직전에 실행.
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

WINTER_KEYWORDS = ["패딩", "롱패딩", "기모", "퍼코트", "무스탕", "울코트", "방한", "털"]
SUMMER_KEYWORDS = ["민소매", "나시", "슬리브리스", "린넨반팔"]


def qa_check(
    outfits: list[dict],
    user_gender: str = "",
    user_tpo_list: list[str] | None = None,
    current_month: int | None = None,
) -> list[dict]:
    """최종 QA 검증. 문제 코디를 제거하고 로그를 남긴다."""
    if current_month is None:
        current_month = datetime.now().month
    if user_tpo_list is None:
        user_tpo_list = []

    current_season = _MONTH_TO_SEASON.get(current_month, "spring")

    passed = []
    for outfit in outfits:
        issues = []

        # 1. 성별 크로스체크
        if user_gender and user_gender != "unisex":
            for item in outfit.get("items", []):
                ig = item.get("gender", "unisex")
                if ig != "unisex" and ig != user_gender:
                    issues.append(f"gender:{ig}")

        # 2. 시즌 크로스체크
        if current_season in ("summer", "spring"):
            for item in outfit.get("items", []):
                name = item.get("name", "")
                if any(kw in name for kw in WINTER_KEYWORDS):
                    issues.append(f"winter_item:{name[:20]}")
        elif current_season in ("winter", "autumn"):
            for item in outfit.get("items", []):
                name = item.get("name", "")
                if any(kw in name for kw in SUMMER_KEYWORDS):
                    issues.append(f"summer_item:{name[:20]}")

        # 3. TPO-포멀도 크로스체크
        for tpo in user_tpo_list:
            if tpo.lower() == "interview":
                formalities = [item.get("formality", 3) for item in outfit.get("items", [])]
                if any(f < 4 for f in formalities):
                    issues.append(f"interview_formality:{min(formalities)}")

        if issues:
            oid = outfit.get("outfit_id", "unknown")[:30]
            logger.warning(f"QA FAIL [{oid}]: {'; '.join(issues)}")
            continue

        passed.append(outfit)

    removed = len(outfits) - len(passed)
    if removed > 0:
        logger.info(f"QA Gate: {removed}/{len(outfits)} removed")

    return passed
