"""
아동복/이상 데이터 클렌징 스크립트.

사용법:
    cd backend
    python -m scripts.clean_invalid_outfits
"""

import json
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SCORED_PATH = DATA_DIR / "outfits_scored.json"

KIDS_NAME_KEYWORDS = ["키즈", "아동", "유아", "주니어", "kids", "baby", "베이비", "아기", "어린이"]
KIDS_BRANDS = ["밍크뮤", "래핑차일드", "블루독", "모이몰른", "알로봇"]


def check_outfit(outfit: dict) -> str | None:
    """위반 사유 반환. 정상이면 None."""
    items = outfit.get("items", [])
    total_price = outfit.get("total_price", 0)

    # 1. 아동복 감지
    for it in items:
        name = it.get("name", "").lower()
        brand = it.get("brand", "").lower()
        mall = it.get("mall_name", "").lower()
        for kw in KIDS_NAME_KEYWORDS:
            if kw in name:
                return f"아동복 키워드: '{kw}' in '{it['name'][:40]}'"
        for kb in KIDS_BRANDS:
            if kb in brand or kb in mall:
                return f"아동복 브랜드: '{kb}'"

    # 2. 가격 이상치
    if total_price > 2000000:
        return f"가격 초과: {total_price:,}원"
    if total_price < 10000 and total_price > 0:
        return f"가격 미달: {total_price:,}원"

    # 3. 이미지 유효성
    for it in items:
        url = it.get("image_url", "")
        if not url or url.strip() == "":
            return "빈 이미지 URL"

    # 4. 카테고리 일관성 (1개 아이템 코디)
    if len(items) == 1:
        cat = items[0].get("category", "")
        if cat not in ("원피스", "점프수트"):
            return f"1아이템 코디 (카테고리: {cat})"

    return None


def main():
    # 백업
    backup_path = DATA_DIR / f"outfits_scored_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    shutil.copy2(SCORED_PATH, backup_path)
    print(f"백업: {backup_path.name}")

    with open(SCORED_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"처리 전: {len(data)}건")

    removed = []
    clean = []
    reason_counter = Counter()

    for o in data:
        reason = check_outfit(o)
        if reason:
            removed.append({"outfit_id": o.get("outfit_id", ""), "reason": reason})
            # 사유 분류
            if "아동복" in reason:
                reason_counter["아동복"] += 1
            elif "가격 초과" in reason:
                reason_counter["가격 초과"] += 1
            elif "가격 미달" in reason:
                reason_counter["가격 미달"] += 1
            elif "빈 이미지" in reason:
                reason_counter["빈 이미지"] += 1
            elif "1아이템" in reason:
                reason_counter["1아이템 코디"] += 1
        else:
            clean.append(o)

    # 저장
    with open(SCORED_PATH, "w", encoding="utf-8") as f:
        json.dump(clean, f, ensure_ascii=False)

    # 결과
    print(f"\n제거: {len(removed)}건")
    for reason, cnt in reason_counter.most_common():
        print(f"  {reason}: {cnt}건")

    print(f"\n제거 샘플 (최대 5건):")
    for r in removed[:5]:
        print(f"  {r['outfit_id'][:35]} | {r['reason']}")

    print(f"\n남은 코디: {len(clean)}건")

    tpo_counter = Counter()
    for o in clean:
        for t in o.get("designed_tpo", []):
            tpo_counter[t] += 1
    print(f"TPO 분포:")
    for t, c in tpo_counter.most_common():
        print(f"  {t}: {c}")


if __name__ == "__main__":
    main()
