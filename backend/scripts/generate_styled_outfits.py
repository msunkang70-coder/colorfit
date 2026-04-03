"""
스타일링 엔진 — 템플릿 기반 코디 생성.

기존 아이템 풀에서 TPO별 템플릿에 맞는 코디를 조합 생성.

사용법:
    cd backend
    python -m scripts.generate_styled_outfits
"""

import json
import hashlib
import random
from collections import Counter, defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SCORED_PATH = DATA_DIR / "outfits_scored.json"
TEMPLATE_PATH = DATA_DIR / "styling_templates.json"

random.seed(42)  # 재현성


def extract_item_pool(outfits: list[dict]) -> dict[str, dict[str, list[dict]]]:
    """기존 코디에서 카테고리 × 성별 아이템 풀 추출."""
    pool: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    seen = set()

    for o in outfits:
        oid = o.get("outfit_id", "")
        gender = "female" if "female" in oid else "male" if "male" in oid else "unisex"
        for it in o.get("items", []):
            pid = it.get("product_id", "")
            cat = it.get("category", "")
            if not pid or not cat or pid in seen:
                continue
            if not it.get("image_url", ""):
                continue
            seen.add(pid)
            pool[cat][gender].append(it)

    return pool


def pick_item(pool: dict, category: str, gender: str) -> dict | None:
    """카테고리에서 아이템 1개 랜덤 선택."""
    items = pool.get(category, {}).get(gender, [])
    if not items:
        items = pool.get(category, {}).get("unisex", [])
    if not items:
        # 다른 성별에서 차용
        for g in pool.get(category, {}):
            if pool[category][g]:
                items = pool[category][g]
                break
    if not items:
        return None
    return random.choice(items)


def make_outfit_id(tpo: str, gender: str, template_name: str, idx: int) -> str:
    h = hashlib.md5(f"{tpo}_{gender}_{template_name}_{idx}".encode()).hexdigest()[:8]
    return f"styled_{tpo}_{gender}_{h}"


def main():
    with open(SCORED_PATH, "r", encoding="utf-8") as f:
        existing = json.load(f)

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        templates = json.load(f)

    print(f"기존 코디: {len(existing)}건")

    # 아이템 풀 추출
    pool = extract_item_pool(existing)
    print(f"아이템 풀: {sum(sum(len(v) for v in cats.values()) for cats in pool.values())}개")
    for cat in sorted(pool.keys()):
        total = sum(len(v) for v in pool[cat].values())
        print(f"  {cat}: {total}개")

    # 기존 outfit_id 수집 (중복 방지)
    existing_ids = {o.get("outfit_id") for o in existing}

    new_outfits = []
    stats = Counter()

    for tpo, genders in templates.items():
        for gender, tmpls in genders.items():
            for tmpl in tmpls:
                slots = tmpl["slots"]
                name = tmpl["name"]

                # 각 템플릿에서 최대 5개 코디 생성 시도
                for idx in range(5):
                    items = []
                    success = True
                    used_pids = set()

                    for cat in slots:
                        it = pick_item(pool, cat, gender)
                        if not it or it.get("product_id") in used_pids:
                            success = False
                            break
                        items.append(it)
                        used_pids.add(it.get("product_id"))

                    if not success or len(items) != len(slots):
                        continue

                    oid = make_outfit_id(tpo, gender, name, idx)
                    if oid in existing_ids:
                        continue

                    total_price = sum(it.get("price", 0) for it in items)
                    formalities = [it.get("formality", 3) for it in items]
                    avg_f = sum(formalities) / len(formalities)

                    outfit = {
                        "outfit_id": oid,
                        "items": items,
                        "designed_tpo": [tpo],
                        "tags": [tpo, "spring", "autumn"],
                        "total_price": total_price,
                        "is_complete_outfit": True,
                        "template": name,
                    }

                    new_outfits.append(outfit)
                    existing_ids.add(oid)
                    stats[f"{tpo}_{gender}"] += 1

    # 기존 데이터에 추가
    combined = existing + new_outfits

    with open(SCORED_PATH, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False)

    print(f"\n=== 생성 결과 ===")
    print(f"새 코디: {len(new_outfits)}건")
    print(f"최종 코디: {len(combined)}건")
    print(f"\nTPO별:")
    tpo_counter = Counter()
    for o in combined:
        for t in o.get("designed_tpo", []):
            tpo_counter[t] += 1
    for t, c in tpo_counter.most_common():
        print(f"  {t}: {c}")

    # 새 코디 샘플
    print(f"\n=== 샘플 ===")
    for tpo in ["interview", "commute", "date", "workout"]:
        samples = [o for o in new_outfits if tpo in o.get("designed_tpo", [])][:1]
        for o in samples:
            cats = [it.get("category") for it in o.get("items", [])]
            names = [it.get("name", "")[:25] for it in o.get("items", [])]
            print(f"  {tpo}: {cats} ₩{o['total_price']:,}")
            for n in names:
                print(f"    {n}")


if __name__ == "__main__":
    main()
