"""
종합 데이터 클렌징 + 시즌 태그 정제 스크립트 (v3).

사용법:
    cd backend
    python -m scripts.clean_and_refine_data
"""

import json
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SCORED_PATH = DATA_DIR / "outfits_scored.json"

# ── 시즌 규칙 (교집합 방식) ──

WINTER_ONLY_KW = ["패딩", "롱패딩", "기모", "퍼코트", "무스탕", "울코트", "터틀넥", "방한", "털", "플리스", "다운"]
SUMMER_ONLY_KW = ["민소매", "반팔", "린넨", "크롭탑", "슬리브리스", "나시", "숏팬츠", "탱크탑"]
SPRING_AUTUMN_KW = ["가디건", "자켓", "블레이저", "트렌치", "바람막이", "간절기"]

CAT_SEASONS = {
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
    "숏팬츠": ["summer"],
    "반바지": ["summer"],
    "레깅스": ["spring", "summer", "autumn", "winter"],
    "셔츠": ["spring", "summer", "autumn", "winter"],
    "블라우스": ["spring", "summer", "autumn", "winter"],
    "슬랙스": ["spring", "summer", "autumn", "winter"],
    "스커트": ["spring", "summer", "autumn", "winter"],
    "청바지": ["spring", "summer", "autumn", "winter"],
    "원피스": ["spring", "summer", "autumn"],
    "로퍼": ["spring", "summer", "autumn", "winter"],
    "힐": ["spring", "summer", "autumn", "winter"],
    "스니커즈": ["spring", "summer", "autumn", "winter"],
}

KIDS_KW = ["키즈", "아동", "유아", "주니어", "kids", "baby", "베이비", "아기", "어린이"]
KIDS_BRANDS = ["밍크뮤", "래핑차일드", "블루독", "모이몰른", "알로봇"]


def get_item_seasons(item: dict) -> set[str]:
    """아이템 1개의 착용 가능 시즌."""
    cat = item.get("category", "")
    name = item.get("name", "").lower()

    # 이름 키워드 우선
    for kw in WINTER_ONLY_KW:
        if kw in name:
            return {"winter"}
    for kw in SUMMER_ONLY_KW:
        if kw in name:
            return {"summer"}
    for kw in SPRING_AUTUMN_KW:
        if kw in name:
            return {"spring", "autumn"}

    # 카테고리 기반
    if cat in CAT_SEASONS:
        return set(CAT_SEASONS[cat])

    return {"spring", "summer", "autumn", "winter"}


def compute_outfit_seasons(outfit: dict) -> list[str]:
    """코디의 시즌 = 아이템 시즌의 교집합."""
    items = outfit.get("items", [])
    if not items:
        return ["spring", "summer", "autumn", "winter"]

    result = get_item_seasons(items[0])
    for it in items[1:]:
        result = result & get_item_seasons(it)

    # 교집합이 비면 union fallback
    if not result:
        result = set()
        for it in items:
            result |= get_item_seasons(it)

    return sorted(result)


def check_removal(outfit: dict) -> str | None:
    """제거 사유 반환. 정상이면 None."""
    items = outfit.get("items", [])
    total_price = outfit.get("total_price", 0)

    # 아동복
    for it in items:
        name = it.get("name", "").lower()
        brand = it.get("brand", "").lower()
        mall = it.get("mall_name", "").lower()
        for kw in KIDS_KW:
            if kw in name:
                return f"아동복: '{kw}'"
        for kb in KIDS_BRANDS:
            if kb in brand or kb in mall:
                return f"아동복 브랜드: '{kb}'"

    # 가격
    if total_price > 2000000:
        return f"가격 초과: {total_price:,}원"
    if 0 < total_price < 10000:
        return f"가격 미달: {total_price:,}원"

    # 이미지
    for it in items:
        if not it.get("image_url", "").strip():
            return "빈 이미지"

    # 단품
    if len(items) == 1 and items[0].get("category", "") not in ("원피스", "점프수트"):
        return "단품 코디"

    # 성별 크로스체크
    oid = outfit.get("outfit_id", "")
    outfit_gender = "female" if "female" in oid else "male" if "male" in oid else ""
    if outfit_gender:
        for it in items:
            ig = it.get("gender", "unisex")
            if ig != "unisex" and ig != outfit_gender:
                return f"성별 불일치: outfit={outfit_gender}, item={ig}"

    return None


def main():
    backup_path = DATA_DIR / f"outfits_scored_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    shutil.copy2(SCORED_PATH, backup_path)
    print(f"백업: {backup_path.name}")

    with open(SCORED_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"처리 전: {len(data)}건")

    # 시즌 태그 변경 전 통계
    before_4season = sum(1 for o in data if len(set(o.get("tags", [])) & {"spring","summer","autumn","winter"}) == 4)
    before_3season = sum(1 for o in data if len(set(o.get("tags", [])) & {"spring","summer","autumn","winter"}) == 3)

    # 1. 시즌 태그 정제
    season_changed = 0
    for o in data:
        new_seasons = compute_outfit_seasons(o)
        old_tags = set(o.get("tags", []))
        old_seasons = old_tags & {"spring", "summer", "autumn", "winter"}
        new_season_set = set(new_seasons)
        if old_seasons != new_season_set:
            season_changed += 1
        # 기존 비시즌 태그 유지 + 새 시즌 태그
        non_season = old_tags - {"spring", "summer", "autumn", "winter"}
        o["tags"] = sorted(non_season | new_season_set)

    after_4season = sum(1 for o in data if len(set(o.get("tags", [])) & {"spring","summer","autumn","winter"}) == 4)
    after_3season = sum(1 for o in data if len(set(o.get("tags", [])) & {"spring","summer","autumn","winter"}) == 3)

    print(f"\n시즌 태그 정제: {season_changed}건 변경")
    print(f"  변경 전: 4시즌={before_4season}, 3시즌={before_3season}")
    print(f"  변경 후: 4시즌={after_4season}, 3시즌={after_3season}")

    # 2. 포멀도 기반 TPO 제거
    interview_removed = 0
    commute_removed = 0
    for o in data:
        items = o.get("items", [])
        formalities = [it.get("formality", 3) for it in items]
        avg_f = sum(formalities) / len(formalities) if formalities else 3
        dtpo = o.get("designed_tpo", [])

        if "interview" in dtpo:
            if any(f < 4 for f in formalities):
                dtpo.remove("interview")
                interview_removed += 1
        if "commute" in dtpo:
            if avg_f < 3.5:
                dtpo.remove("commute")
                commute_removed += 1
        o["designed_tpo"] = dtpo

    print(f"\n포멀도 기반 TPO 제거:")
    print(f"  interview에서 제거: {interview_removed}건")
    print(f"  commute에서 제거: {commute_removed}건")

    # 3. 기존 클렌징
    removal_counter = Counter()
    clean = []
    for o in data:
        reason = check_removal(o)
        if reason:
            if "아동복" in reason: removal_counter["아동복"] += 1
            elif "가격" in reason: removal_counter["가격 이상"] += 1
            elif "이미지" in reason: removal_counter["빈 이미지"] += 1
            elif "단품" in reason: removal_counter["단품 코디"] += 1
            elif "성별" in reason: removal_counter["성별 불일치"] += 1
        else:
            # designed_tpo가 비면 제거
            if not o.get("designed_tpo"):
                removal_counter["TPO 없음"] += 1
            else:
                clean.append(o)

    print(f"\n제거 내역:")
    for reason, cnt in removal_counter.most_common():
        print(f"  {reason}: {cnt}건")

    # 저장
    with open(SCORED_PATH, "w", encoding="utf-8") as f:
        json.dump(clean, f, ensure_ascii=False)

    # 최종 통계
    tpo_counter = Counter()
    season_counter = Counter()
    for o in clean:
        for t in o.get("designed_tpo", []):
            tpo_counter[t] += 1
        for s in set(o.get("tags", [])) & {"spring", "summer", "autumn", "winter"}:
            season_counter[s] += 1

    print(f"\n최종 코디: {len(clean)}건")
    print(f"TPO 분포: {dict(tpo_counter.most_common())}")
    print(f"시즌 분포: {dict(season_counter.most_common())}")


if __name__ == "__main__":
    main()
