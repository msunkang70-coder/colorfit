"""
workout 코디 보강 — casual/weekend 코디 중 활동적 아이템을 workout으로 복제/변환.

사용법:
    cd backend
    python -m scripts.generate_workout_outfits
"""

import copy
import json
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SCORED_PATH = DATA_DIR / "outfits_scored.json"

# workout에 적합한 카테고리
WORKOUT_CATS = {"티셔츠", "맨투맨", "후드", "탱크탑", "크롭탑", "머슬핏",
                "레깅스", "조거팬츠", "숏팬츠", "반바지", "스니커즈"}

# workout에 부적합한 카테고리
WORKOUT_FORBIDDEN = {"원피스", "블라우스", "코트", "자켓", "패딩", "힐", "로퍼",
                     "슬랙스", "스커트", "셔츠", "점프수트", "가디건"}

# workout에 부적합한 상품명 키워드
WORKOUT_NAME_FORBIDDEN = ["원피스", "드레스", "블라우스", "코트", "자켓", "패딩",
                          "정장", "면접", "오피스"]


def is_workout_compatible(outfit: dict) -> bool:
    """이 코디가 workout으로 변환 가능한지 판단."""
    items = outfit.get("items", [])
    cats = {it.get("category", "") for it in items}

    # 금지 카테고리 포함 시 불가
    if cats & WORKOUT_FORBIDDEN:
        return False

    # 최소 1개 이상 workout 적합 카테고리 필요
    if not (cats & WORKOUT_CATS):
        return False

    # 상품명 체크
    for it in items:
        name = it.get("name", "").lower()
        for kw in WORKOUT_NAME_FORBIDDEN:
            if kw in name:
                return False

    return True


def main():
    with open(SCORED_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 현재 workout 수
    existing_workout = [o for o in data if "workout" in o.get("designed_tpo", [])]
    print(f"현재 workout 코디: {len(existing_workout)}")

    # casual/weekend 코디에서 workout 호환 찾기
    source_tpos = {"casual", "weekend", "campus", "daily"}
    candidates = []
    for o in data:
        tpo_set = set(o.get("designed_tpo", []))
        if tpo_set & source_tpos and "workout" not in tpo_set:
            if is_workout_compatible(o):
                candidates.append(o)

    print(f"workout 변환 가능 후보: {len(candidates)}")

    # 필요한 수만큼 변환
    target = 50
    needed = max(0, target - len(existing_workout))
    to_convert = candidates[:needed]

    new_outfits = []
    for o in to_convert:
        new = copy.deepcopy(o)
        new["outfit_id"] = o["outfit_id"] + "_workout"
        new["designed_tpo"] = ["workout"]
        # tags 업데이트
        tags = set(new.get("tags", []))
        tags.discard("casual")
        tags.discard("weekend")
        tags.discard("campus")
        tags.add("workout")
        tags.add("street")
        new["tags"] = sorted(tags)
        new_outfits.append(new)

    data.extend(new_outfits)

    with open(SCORED_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    # 결과 통계
    tpo_counter = Counter()
    for o in data:
        for t in o.get("designed_tpo", []):
            tpo_counter[t] += 1

    print(f"\n추가: {len(new_outfits)}건")
    print(f"총 코디: {len(data)}")
    print(f"\nTPO 분포:")
    for t, c in tpo_counter.most_common():
        print(f"  {t}: {c}")


if __name__ == "__main__":
    main()
