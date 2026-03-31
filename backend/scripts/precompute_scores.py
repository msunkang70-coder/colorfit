"""
스코어 프리컴퓨팅 — 전체 코디에 대해 기본 5축 스코어 사전 계산.
런타임에는 개인화 보정만 적용한다.
기획서: outfits.scores JSONB에 저장.

사용법:
    python -m scripts.precompute_scores
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.services.scoring import (
    calculate_pcf,
    calculate_of,
    calculate_ch,
    calculate_pe,
    calculate_sf,
    TONE_IDS,
)
from app.services.style_filter import filter_outfit

DATA_DIR = PROJECT_ROOT / "data"


def load_product_map() -> dict[str, dict]:
    """전체 상품 맵 로드 (product_id → product dict)."""
    product_map: dict[str, dict] = {}
    normalized_dir = DATA_DIR / "normalized"

    for tone_file in sorted(normalized_dir.glob("*.json")):
        if tone_file.name == "all_products.json":
            continue
        with open(tone_file, "r", encoding="utf-8") as f:
            products = json.load(f)
        for p in products:
            pid = p.get("product_id", "")
            if pid:
                product_map[pid] = p

    # all_products.json도 시도
    all_path = normalized_dir / "all_products.json"
    if all_path.exists():
        with open(all_path, "r", encoding="utf-8") as f:
            for p in json.load(f):
                pid = p.get("product_id", "")
                if pid and pid not in product_map:
                    product_map[pid] = p

    return product_map


def enrich_outfit(outfit: dict, product_map: dict[str, dict]) -> dict:
    """코디 아이템에 상품 정보를 보충한다."""
    enriched_items = []
    for item in outfit.get("items", []):
        pid = item.get("product_id", "")
        product = product_map.get(pid, {})

        enriched = {**item}
        # 누락 필드 보충
        if not enriched.get("tone_id"):
            enriched["tone_id"] = product.get("tone_id", outfit.get("tone_id", ""))
        if not enriched.get("color_hex"):
            colors = product.get("color_hex", [])
            enriched["color_hex"] = colors[0] if isinstance(colors, list) and colors else ""
        if not enriched.get("brand"):
            enriched["brand"] = product.get("brand", product.get("mall_name", ""))
        if not enriched.get("gender"):
            enriched["gender"] = product.get("gender", outfit.get("gender", "unisex"))
        if not enriched.get("mall_name"):
            enriched["mall_name"] = product.get("mall_name", "")
        if not enriched.get("mall_url"):
            enriched["mall_url"] = product.get("mall_url", "")
        if not enriched.get("title") and not enriched.get("name"):
            enriched["name"] = product.get("name", "")

        enriched_items.append(enriched)

    outfit["items"] = enriched_items

    # 코디 레벨 태그 보충
    if not outfit.get("tags"):
        tags = []
        tpo = outfit.get("designed_tpo", "")
        if isinstance(tpo, str) and tpo:
            tags.append(tpo)
        elif isinstance(tpo, list):
            tags.extend(tpo)
        moods = outfit.get("designed_moods", [])
        if moods:
            tags.extend(moods)
        outfit["tags"] = tags

    # designed_tpo를 리스트로 정규화
    tpo = outfit.get("designed_tpo", [])
    if isinstance(tpo, str):
        outfit["designed_tpo"] = [tpo] if tpo else []

    # total_price 보충
    if not outfit.get("total_price"):
        outfit["total_price"] = outfit.get("price_total", 0)

    return outfit


def compute_scores_for_tone(
    outfit: dict,
    tone_id: str,
) -> dict[str, float]:
    """특정 톤 사용자 기준으로 기본 스코어를 계산한다."""
    items = outfit.get("items", [])

    # PCF
    item_tone_ids = [it.get("tone_id") for it in items]
    raw_colors = [it.get("color_hex", "#808080") for it in items]
    # 빈 문자열이나 리스트 → 기본 회색
    item_hex_colors = []
    for c in raw_colors:
        if isinstance(c, list):
            c = c[0] if c else ""
        if not c or len(c.lstrip("#")) < 6:
            c = "#808080"
        item_hex_colors.append(c)

    pcf = calculate_pcf(item_tone_ids, item_hex_colors, tone_id)

    # OF — 기본 TPO로 계산 (런타임에 사용자 TPO로 재계산)
    outfit_tags = outfit.get("designed_tpo", [])
    if isinstance(outfit_tags, str):
        outfit_tags = [outfit_tags]
    of = calculate_of(outfit_tags, outfit_tags)  # 자기 자신과 매칭 → 최고점

    # CH
    valid_colors = [c for c in item_hex_colors if c != "#808080"]
    ch = calculate_ch(valid_colors) if len(valid_colors) >= 2 else 70.0

    # PE — 기본 예산 없이 중간값
    pe = 70.0  # 런타임에 사용자 예산으로 재계산

    # SF
    categories = [it.get("category", "unknown") for it in items]
    top_sil = None
    bot_sil = None
    for it in items:
        sil = it.get("silhouette", "regular")
        cat = it.get("category", "")
        if cat in {"블라우스", "셔츠", "니트", "티셔츠", "맨투맨", "후드", "크롭탑"}:
            top_sil = top_sil or sil
        elif cat in {"슬랙스", "청바지", "스커트", "와이드팬츠", "레깅스"}:
            bot_sil = bot_sil or sil
    sf = calculate_sf(categories, top_sil, bot_sil)

    # StyleFilter 통과 여부
    style_passed, _, style_details = filter_outfit(items)

    total = pcf * 0.25 + of * 0.20 + ch * 0.15 + pe * 0.15 + sf * 0.25

    return {
        "pcf": round(pcf, 2),
        "of": round(of, 2),
        "ch": round(ch, 2),
        "pe": round(pe, 2),
        "sf": round(sf, 2),
        "total": round(total, 2),
        "style_passed": style_passed,
    }


def main():
    print("Loading product map...")
    product_map = load_product_map()
    print(f"  {len(product_map)} products loaded")

    # 코디 로드
    outfits_path = DATA_DIR / "outfits_evaluated.json"
    if not outfits_path.exists():
        outfits_path = DATA_DIR / "outfits.json"

    with open(outfits_path, "r", encoding="utf-8") as f:
        outfits = json.load(f)
    print(f"  {len(outfits)} outfits loaded")

    # 보충 + 스코어 계산
    print("Computing scores...")
    computed = 0
    for outfit in outfits:
        enrich_outfit(outfit, product_map)

        tone_id = outfit.get("tone_id", "")
        if tone_id and tone_id in TONE_IDS:
            scores = compute_scores_for_tone(outfit, tone_id)
            outfit["scores"] = scores
            computed += 1

    print(f"  {computed}/{len(outfits)} outfits scored")

    # 저장
    output_path = DATA_DIR / "outfits_scored.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(outfits, f, ensure_ascii=False, indent=2)

    print(f"Saved to {output_path}")

    # 통계
    scored = [o for o in outfits if o.get("scores")]
    if scored:
        totals = [o["scores"]["total"] for o in scored]
        print(f"\nScore stats:")
        print(f"  Mean: {sum(totals)/len(totals):.1f}")
        print(f"  Min:  {min(totals):.1f}")
        print(f"  Max:  {max(totals):.1f}")

        passed = sum(1 for o in scored if o["scores"].get("style_passed", True))
        print(f"  StyleFilter passed: {passed}/{len(scored)} ({passed/len(scored)*100:.1f}%)")


if __name__ == "__main__":
    main()
