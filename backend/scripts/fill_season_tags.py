"""
시즌 태그 자동 태깅 — 아이템 카테고리/상품명 기반으로 시즌 태그를 추가한다.

사용법:
    cd backend
    python -m scripts.fill_season_tags
"""

import json
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SCORED_PATH = DATA_DIR / "outfits_scored.json"

# 키워드 → 시즌 매핑
WINTER_KEYWORDS = ["패딩", "코트", "플리스", "기모", "털", "양모", "다운", "퍼", "방한", "겨울"]
SUMMER_KEYWORDS = ["반팔", "린넨", "반바지", "숏팬츠", "샌들", "크롭", "탱크탑", "나시", "여름", "시원"]
SPRING_AUTUMN_KEYWORDS = ["니트", "가디건", "트렌치", "바람막이", "간절기"]
THREE_SEASON_KEYWORDS = ["맨투맨", "후드", "청바지", "스웨트"]
ALL_SEASON_CATS = {"셔츠", "블라우스", "슬랙스", "스커트", "로퍼", "힐"}

# 카테고리 → 시즌
CAT_SEASON_MAP = {
    "패딩": ["winter"],
    "코트": ["autumn", "winter"],
    "플리스": ["winter"],
    "니트": ["autumn", "winter", "spring"],
    "가디건": ["spring", "autumn"],
    "자켓": ["spring", "autumn"],
    "후드": ["spring", "autumn", "winter"],
    "맨투맨": ["spring", "autumn", "winter"],
    "티셔츠": ["spring", "summer", "autumn"],
    "크롭탑": ["summer"],
    "탱크탑": ["summer"],
    "반바지": ["summer"],
    "숏팬츠": ["summer"],
    "레깅스": ["spring", "summer", "autumn", "winter"],
    "원피스": ["spring", "summer", "autumn"],
}


def detect_seasons(outfit: dict) -> list[str]:
    """코디의 아이템들을 분석하여 적합한 시즌 목록을 반환."""
    seasons = set()
    items = outfit.get("items", [])

    for it in items:
        cat = it.get("category", "")
        name = it.get("name", "").lower()

        # 카테고리 기반
        if cat in CAT_SEASON_MAP:
            seasons.update(CAT_SEASON_MAP[cat])

        # 상품명 키워드 기반
        for kw in WINTER_KEYWORDS:
            if kw in name:
                seasons.add("winter")
        for kw in SUMMER_KEYWORDS:
            if kw in name:
                seasons.add("summer")
        for kw in SPRING_AUTUMN_KEYWORDS:
            if kw in name:
                seasons.update(["spring", "autumn"])

    # 시즌 감지 못하면 전체
    if not seasons:
        seasons = {"spring", "summer", "autumn", "winter"}

    return sorted(seasons)


def main():
    with open(SCORED_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    season_counter = Counter()
    multi_season = 0
    tagged = 0

    for o in data:
        seasons = detect_seasons(o)

        # 기존 tags에 시즌 태그 추가 (중복 방지)
        existing_tags = set(o.get("tags", []))
        season_set = set(seasons)
        # 기존 시즌 태그 제거 후 새로 추가
        existing_tags -= {"spring", "summer", "autumn", "winter"}
        existing_tags |= season_set
        o["tags"] = sorted(existing_tags)

        for s in seasons:
            season_counter[s] += 1
        if len(seasons) > 1:
            multi_season += 1
        tagged += 1

    with open(SCORED_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    print(f"=== 시즌 태깅 결과 ===")
    print(f"총 코디: {len(data)}")
    print(f"태깅 완료: {tagged}")
    print(f"시즌별 분포:")
    for s in ["spring", "summer", "autumn", "winter"]:
        print(f"  {s}: {season_counter[s]}")
    print(f"멀티시즌 코디: {multi_season}")


if __name__ == "__main__":
    main()
