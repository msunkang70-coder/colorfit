"""
스타일링 엔진 v2 — 품질 기반 코디 생성.

1. 아이템 품질 점수 산정 (브랜드/가격/이름 기반)
2. 템플릿별 고품질 아이템만 조합
3. 코디 점수 프리컴퓨팅
4. 기존 저품질 styled_ 코디 교체

사용법:
    cd backend
    python -m scripts.rebuild_styled_outfits
"""

import json
import hashlib
import random
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SCORED_PATH = DATA_DIR / "outfits_scored.json"
TEMPLATE_PATH = DATA_DIR / "styling_templates.json"

random.seed(42)

# ── 아이템 품질 점수 ──

LOW_QUALITY_BRANDS = ["temu", "쿠팡", "11번가", "위메프", "알리익스프레스", "알리"]
LOW_QUALITY_KEYWORDS = ["자전거", "겨울자전거", "방한화", "작업복", "안전화", "스카프", "매트리스",
                        "침대", "커튼", "이불", "수면", "잠옷", "강아지", "반려", "엄마", "할머니", "중년"]
HIGH_QUALITY_BRANDS = ["코스", "cos", "빈폴", "헤지스", "타미힐피거", "폴로", "마시모두띠",
                       "잇미샤", "리스트", "에잇세컨즈", "무신사 스탠다드", "지오다노",
                       "캘빈클라인", "h&m", "자라", "zara"]


def item_quality_score(item: dict) -> float:
    """아이템 품질 점수 (0~100)."""
    score = 50.0  # 기본
    name = item.get("name", "").lower()
    brand = item.get("brand", "").lower()
    mall = item.get("mall_name", "").lower()
    combined = f"{name} {brand} {mall}"
    price = item.get("price", 0)

    # 저품질 브랜드 감점
    for lb in LOW_QUALITY_BRANDS:
        if lb in combined:
            score -= 30
            break

    # 저품질 키워드 감점
    for kw in LOW_QUALITY_KEYWORDS:
        if kw in name:
            score -= 40
            break

    # 고품질 브랜드 가산
    for hb in HIGH_QUALITY_BRANDS:
        if hb in combined:
            score += 25
            break

    # 가격 기반 (극단 저가/고가 감점)
    if price < 10000:
        score -= 15
    elif price > 500000:
        score -= 10
    elif 30000 <= price <= 200000:
        score += 10

    # 이미지 존재
    if not item.get("image_url"):
        score -= 50

    return max(0, min(100, score))


def pick_best_item(items: list[dict], used_pids: set) -> dict | None:
    """품질 점수가 높은 아이템 중 미사용 1개 선택."""
    candidates = [(it, item_quality_score(it)) for it in items if it.get("product_id") not in used_pids]
    if not candidates:
        return None
    # 상위 5개 중 랜덤 (다양성)
    candidates.sort(key=lambda x: x[1], reverse=True)
    top = candidates[:min(5, len(candidates))]
    chosen = random.choice(top)
    return chosen[0] if chosen[1] >= 30 else None  # 30점 미만은 제외


def main():
    with open(SCORED_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        templates = json.load(f)

    # 기존 styled_ 코디 제거
    base = [o for o in data if not o.get("outfit_id", "").startswith("styled_")]
    removed_styled = len(data) - len(base)
    print(f"기존 styled_ 코디 제거: {removed_styled}건")
    print(f"베이스 코디: {len(base)}건")

    # 아이템 풀 추출 (카테고리 × 성별)
    pool: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    seen = set()
    for o in base:
        oid = o.get("outfit_id", "")
        gender = "female" if "female" in oid else "male" if "male" in oid else "unisex"
        for it in o.get("items", []):
            pid = it.get("product_id", "")
            cat = it.get("category", "")
            if not pid or not cat or pid in seen:
                continue
            if item_quality_score(it) < 30:
                continue  # 저품질 아이템 풀에서 제외
            seen.add(pid)
            pool[cat][gender].append(it)

    total_pool = sum(sum(len(v) for v in cats.values()) for cats in pool.values())
    print(f"고품질 아이템 풀: {total_pool}개")

    # 템플릿 기반 코디 생성
    new_outfits = []
    existing_ids = {o.get("outfit_id") for o in base}

    for tpo, genders in templates.items():
        for gender, tmpls in genders.items():
            for tmpl in tmpls:
                slots = tmpl["slots"]
                name = tmpl["name"]

                for idx in range(8):  # 템플릿당 최대 8개 시도
                    items = []
                    used_pids = set()
                    success = True

                    for cat in slots:
                        cat_items = pool.get(cat, {}).get(gender, [])
                        if not cat_items:
                            cat_items = pool.get(cat, {}).get("unisex", [])
                        if not cat_items:
                            for g in pool.get(cat, {}):
                                if pool[cat][g]:
                                    cat_items = pool[cat][g]
                                    break
                        if not cat_items:
                            success = False
                            break

                        it = pick_best_item(cat_items, used_pids)
                        if not it:
                            success = False
                            break
                        items.append(it)
                        used_pids.add(it.get("product_id"))

                    if not success or len(items) != len(slots):
                        continue

                    # 코디 품질 점수
                    outfit_quality = sum(item_quality_score(it) for it in items) / len(items)
                    if outfit_quality < 50:
                        continue

                    h = hashlib.md5(f"{tpo}_{gender}_{name}_{idx}_v2".encode()).hexdigest()[:8]
                    oid = f"styled_{tpo}_{gender}_{h}"
                    if oid in existing_ids:
                        continue

                    total_price = sum(it.get("price", 0) for it in items)
                    formalities = [it.get("formality", 3) for it in items]

                    outfit = {
                        "outfit_id": oid,
                        "items": items,
                        "designed_tpo": [tpo],
                        "tags": [tpo, "spring", "autumn"],
                        "total_price": total_price,
                        "is_complete_outfit": True,
                        "template": name,
                        "quality_score": round(outfit_quality, 1),
                    }
                    new_outfits.append(outfit)
                    existing_ids.add(oid)

    combined = base + new_outfits
    with open(SCORED_PATH, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False)

    # 통계
    from collections import Counter
    tpo_counter = Counter()
    for o in combined:
        for t in o.get("designed_tpo", []):
            tpo_counter[t] += 1

    print(f"\n새 코디: {len(new_outfits)}건 (품질 필터 적용)")
    print(f"최종: {len(combined)}건")
    print(f"\nTPO 분포:")
    for t, c in tpo_counter.most_common():
        print(f"  {t}: {c}")

    # 품질 샘플
    print(f"\n=== 고품질 샘플 ===")
    for tpo in ["interview", "commute", "date"]:
        samples = [o for o in new_outfits if tpo in o.get("designed_tpo", [])]
        if samples:
            o = max(samples, key=lambda x: x.get("quality_score", 0))
            cats = [it.get("category") for it in o.get("items", [])]
            brands = [it.get("brand", "")[:12] for it in o.get("items", [])]
            print(f"  {tpo}: {cats} | brands={brands} | ₩{o['total_price']:,} | quality={o['quality_score']}")


if __name__ == "__main__":
    main()
