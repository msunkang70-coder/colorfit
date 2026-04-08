"""남성 코디에서 여성 요소 완전 제거.

문제:
1. 남성 코디에 여성 전용 카테고리(스커트, 블라우스, 원피스 등) 포함
2. 남성 코디 아이템의 gender=female 잔존
3. 여성 코디에 남성 전용 카테고리 포함 가능성

해결:
1. 여성 전용 카테고리 → 남성 대체 카테고리로 교체
2. 아이템 gender 필드를 코디 gender로 통일
3. 교체된 아이템에 normalized 풀에서 이미지 매핑
"""

import json
import random
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
random.seed(42)

# 여성 전용 → 남성 대체 카테고리 매핑
FEMALE_TO_MALE_CAT = {
    "스커트": "슬랙스",
    "원피스": "셔츠",
    "블라우스": "셔츠",
    "힐": "로퍼",
    "크롭탑": "티셔츠",
    "레깅스": "조거팬츠",
    "스포츠브라": "반팔티",
}

# 남성 전용 → 여성 대체 카테고리 매핑
MALE_TO_FEMALE_CAT = {
    "넥타이": "스카프",
}

# 카테고리별 기본 포멀도
CAT_FORMALITY = {
    "슬랙스": 3.5, "셔츠": 3.5, "로퍼": 3.5, "티셔츠": 2.0,
    "조거팬츠": 1.5, "반팔티": 1.5, "스카프": 3.0,
}


def build_image_pool(outfits):
    """기존 코디 아이템에서 성별×카테고리별 이미지 풀 구축."""
    pool = defaultdict(list)  # (gender, category) -> [image_url]
    for o in outfits:
        gender = o.get("gender", "")
        for it in o.get("items", []):
            img = it.get("image_url", "").strip()
            cat = it.get("category", "")
            if img and cat and it.get("gender", "") == gender:
                pool[(gender, cat)].append(img)
    # normalized 풀도 추가
    norm_dir = DATA_DIR / "normalized"
    if norm_dir.exists():
        for f in norm_dir.glob("*.json"):
            items = json.loads(f.read_text(encoding="utf-8"))
            for it in items:
                img = it.get("image_url", "").strip()
                cat = it.get("category", "")
                g = it.get("gender", "unisex")
                if img and cat:
                    pool[(g, cat)].append(img)
                    if g == "unisex":
                        pool[("male", cat)].append(img)
                        pool[("female", cat)].append(img)
    return pool


def main():
    print("=" * 60)
    print("남성/여성 코디 성별 누수 수정")
    print("=" * 60)

    # 백업
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(DATA_DIR / "outfits_scored.json", DATA_DIR / f"outfits_scored_backup_{ts}.json")

    outfits = json.loads((DATA_DIR / "outfits_scored.json").read_text(encoding="utf-8"))
    print(f"로드: {len(outfits)}개")

    img_pool = build_image_pool(outfits)

    cat_replaced = 0
    gender_fixed = 0
    img_fixed = 0

    for o in outfits:
        outfit_gender = o.get("gender", "")
        if not outfit_gender:
            continue

        cat_map = FEMALE_TO_MALE_CAT if outfit_gender == "male" else MALE_TO_FEMALE_CAT

        for it in o.get("items", []):
            cat = it.get("category", "")

            # 1) 여성/남성 전용 카테고리 교체
            if cat in cat_map:
                new_cat = cat_map[cat]
                it["category"] = new_cat
                it["formality"] = CAT_FORMALITY.get(new_cat, it.get("formality", 3))
                # 이미지도 교체
                candidates = img_pool.get((outfit_gender, new_cat), [])
                if candidates:
                    it["image_url"] = random.choice(candidates)
                    img_fixed += 1
                it["name"] = it.get("name", "").replace(cat, new_cat)
                it["title"] = ""  # 타이틀 초기화 (이미지 교체 시 새 타이틀 매핑)
                cat_replaced += 1

            # 2) 아이템 gender 통일
            if it.get("gender", "") != outfit_gender and it.get("gender", "") != "unisex":
                it["gender"] = outfit_gender
                gender_fixed += 1

    # formality_avg 재계산
    form_fixed = 0
    for o in outfits:
        items = o.get("items", [])
        if items:
            formals = [it.get("formality", 3) for it in items]
            new_avg = round(sum(formals) / len(formals), 1)
            if o.get("formality_avg") != new_avg:
                o["formality_avg"] = new_avg
                form_fixed += 1

    print(f"\n카테고리 교체: {cat_replaced}개")
    print(f"gender 통일: {gender_fixed}개")
    print(f"이미지 교체: {img_fixed}개")
    print(f"formality 재계산: {form_fixed}개")

    # 저장
    (DATA_DIR / "outfits_scored.json").write_text(
        json.dumps(outfits, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"저장 완료: outfits_scored.json")

    # 검증
    print(f"\n{'=' * 60}")
    print("검증")
    print(f"{'=' * 60}")

    female_cats = set(FEMALE_TO_MALE_CAT.keys())
    male_cats = set(MALE_TO_FEMALE_CAT.keys())

    male_outfits = [o for o in outfits if o.get("gender") == "male"]
    female_outfits = [o for o in outfits if o.get("gender") == "female"]

    # 남성 코디에 여성 카테고리
    m_fcat = sum(1 for o in male_outfits for it in o.get("items", []) if it.get("category") in female_cats)
    # 남성 코디에 gender=female 아이템
    m_fgender = sum(1 for o in male_outfits for it in o.get("items", []) if it.get("gender") == "female")
    # 여성 코디에 남성 카테고리
    f_mcat = sum(1 for o in female_outfits for it in o.get("items", []) if it.get("category") in male_cats)

    print(f"남성 코디 내 여성 카테고리: {m_fcat} (목표 0)")
    print(f"남성 코디 내 gender=female: {m_fgender} (목표 0)")
    print(f"여성 코디 내 남성 카테고리: {f_mcat} (목표 0)")


if __name__ == "__main__":
    main()
