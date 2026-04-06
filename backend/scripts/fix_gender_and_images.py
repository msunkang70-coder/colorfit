"""성별 불일치 수정 + 이미지 없는 코디에 실제 상품 이미지 매핑.

문제:
1. outfit_id에 'female'이 있는데 gender='male'로 잘못 배정 (87개)
2. outfit_id에 'male'이 있는데 gender='female'로 잘못 배정 (65개)
3. 이미지 없는 코디 360개 (특히 workout)

해결:
1. ID 기반으로 gender 정정
2. normalized 상품 풀에서 카테고리+톤 매칭으로 이미지 채움
"""

import json
import random
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
random.seed(42)


def load(name):
    p = DATA_DIR / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def save(name, data):
    p = DATA_DIR / name
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Saved: {name} ({len(data)} items, {p.stat().st_size / 1024:.0f}KB)")


def build_product_pool():
    """normalized 상품 풀에서 카테고리×톤×성별 인덱스 구축."""
    pool = defaultdict(list)  # (category, tone_id, gender) -> [product]
    norm_dir = DATA_DIR / "normalized"
    if not norm_dir.exists():
        print("  WARNING: normalized/ 없음, 기존 코디 아이템에서 풀 구축")
        return pool

    for f in norm_dir.glob("*.json"):
        items = json.loads(f.read_text(encoding="utf-8"))
        for it in items:
            if not it.get("image_url", "").strip():
                continue
            cat = it.get("category", "")
            tone = it.get("tone_id", "")
            gender = it.get("gender", "unisex")
            if cat:
                pool[(cat, tone, gender)].append(it)
                if gender == "unisex":
                    pool[(cat, tone, "male")].append(it)
                    pool[(cat, tone, "female")].append(it)
    print(f"  상품 풀: {sum(len(v) for v in pool.values())} entries")
    return pool


def build_pool_from_outfits(outfits):
    """기존 코디 아이템에서 이미지 있는 것만 풀 구축 (fallback)."""
    pool = defaultdict(list)
    for o in outfits:
        for it in o.get("items", []):
            if it.get("image_url", "").strip():
                cat = it.get("category", "")
                tone = it.get("tone_id", "")
                gender = o.get("gender", "")
                if cat:
                    pool[(cat, tone, gender)].append(it)
                    pool[(cat, "", gender)].append(it)  # tone 무관 fallback
                    pool[(cat, "", "")].append(it)  # 최종 fallback
    print(f"  코디 아이템 풀: {sum(len(v) for v in pool.values())} entries")
    return pool


def find_image(pool, category, tone_id, gender):
    """카테고리+톤+성별로 이미지 찾기 (단계적 완화)."""
    # 1. 정확 매칭
    candidates = pool.get((category, tone_id, gender), [])
    if candidates:
        return random.choice(candidates).get("image_url", "")

    # 2. 톤 무관
    candidates = pool.get((category, "", gender), [])
    if candidates:
        return random.choice(candidates).get("image_url", "")

    # 3. 성별 무관
    candidates = pool.get((category, tone_id, ""), [])
    if candidates:
        return random.choice(candidates).get("image_url", "")

    # 4. 최종 fallback
    candidates = pool.get((category, "", ""), [])
    if candidates:
        return random.choice(candidates).get("image_url", "")

    return ""


def main():
    print("=" * 60)
    print("성별 불일치 수정 + 이미지 매핑")
    print("=" * 60)

    # 백업
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(DATA_DIR / "outfits_scored.json", DATA_DIR / f"outfits_scored_backup_{ts}.json")

    outfits = load("outfits_scored.json")
    print(f"\n[1] 로드: {len(outfits)}개")

    # ── Step 1: Gender 정정 ──
    fixed_gender = 0
    for o in outfits:
        oid = o.get("outfit_id", "")
        gender = o.get("gender", "")
        # ID에 female이 명시되어 있으면 female
        if "_female_" in oid and gender != "female":
            o["gender"] = "female"
            fixed_gender += 1
        # ID에 male이 명시되어 있으면 male (female이 없는 경우)
        elif "_male_" in oid and "_female_" not in oid and gender != "male":
            o["gender"] = "male"
            fixed_gender += 1
    print(f"\n[2] Gender 정정: {fixed_gender}개")

    # ── Step 2: 이미지 매핑 ──
    norm_pool = build_product_pool()
    outfit_pool = build_pool_from_outfits(outfits)
    # 두 풀 합치기
    combined_pool = defaultdict(list)
    for key, items in norm_pool.items():
        combined_pool[key].extend(items)
    for key, items in outfit_pool.items():
        combined_pool[key].extend(items)

    fixed_images = 0
    still_missing = 0
    for o in outfits:
        gender = o.get("gender", "")
        tone = o.get("tone_id", "")
        for it in o.get("items", []):
            if not it.get("image_url", "").strip():
                cat = it.get("category", "")
                img = find_image(combined_pool, cat, tone, gender)
                if img:
                    it["image_url"] = img
                    fixed_images += 1
                else:
                    still_missing += 1

    print(f"[3] 이미지 매핑: {fixed_images}개 채움, {still_missing}개 여전히 없음")

    # ── Step 3: formality_avg 없는 것 보정 ──
    fixed_form = 0
    for o in outfits:
        if not o.get("formality_avg") or o["formality_avg"] == 0:
            items = o.get("items", [])
            formals = [it.get("formality", 3) for it in items]
            if formals:
                o["formality_avg"] = round(sum(formals) / len(formals), 1)
                fixed_form += 1
    print(f"[4] Formality 보정: {fixed_form}개")

    # ── 저장 ──
    save("outfits_scored.json", outfits)

    # ── 검증 ──
    print(f"\n{'='*60}")
    print("검증")
    print(f"{'='*60}")

    # gender 불일치
    mis1 = sum(1 for o in outfits if "_female_" in o.get("outfit_id","") and o.get("gender") != "female")
    mis2 = sum(1 for o in outfits if "_male_" in o.get("outfit_id","") and "_female_" not in o.get("outfit_id","") and o.get("gender") != "male")
    print(f"Gender 불일치: {mis1 + mis2}개 (목표 0)")

    # 이미지
    no_img = sum(1 for o in outfits if not any(it.get("image_url","").strip() for it in o.get("items",[])))
    total_items = sum(len(o.get("items",[])) for o in outfits)
    items_with_img = sum(1 for o in outfits for it in o.get("items",[]) if it.get("image_url","").strip())
    print(f"이미지 없는 코디: {no_img}/{len(outfits)}")
    print(f"아이템 이미지 보유: {items_with_img}/{total_items} ({items_with_img/total_items*100:.1f}%)")

    # workout 남성 상세
    wm = [o for o in outfits
        if o.get("designed_tpo") and "workout" in [t.lower() for t in o["designed_tpo"]]
        and o.get("gender") == "male" and o.get("scores") and o["scores"].get("total")]
    wm_img = sum(1 for o in wm if any(it.get("image_url","").strip() for it in o.get("items",[])))
    print(f"\nWorkout 남성: {len(wm)}개, 이미지 있음: {wm_img}/{len(wm)}")
    for i, o in enumerate(wm[:5]):
        cats = [it.get("category","?") for it in o.get("items",[])]
        has_img = all(it.get("image_url","").strip() for it in o.get("items",[]))
        print(f"  #{i+1} {o['outfit_id'][:40]} | {cats} | img={'ALL' if has_img else 'PARTIAL'}")

    # formality 0 체크
    zero_form = sum(1 for o in outfits if not o.get("formality_avg") or o["formality_avg"] == 0)
    print(f"\nFormality=0: {zero_form}개 (목표 0)")


if __name__ == "__main__":
    main()
