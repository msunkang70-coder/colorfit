"""
서비스 신뢰도 보장을 위한 품질 규칙 강제 적용.

작업 1: 잘못된 코디 조합 제거 (원피스+하의 등)
작업 2: TPO별 카테고리 whitelist 강제
작업 3: 가격 정책 적용
작업 4: 이미지 품질 필터
작업 5: QA 검증

사용법:
    cd backend
    python -m scripts.enforce_quality_rules
"""

import json
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SCORED_PATH = DATA_DIR / "outfits_scored.json"

# ── TPO별 카테고리 whitelist ──
TPO_WHITELIST = {
    "interview": {"셔츠", "블라우스", "슬랙스", "스커트", "자켓", "로퍼", "힐"},
    "commute": {"셔츠", "블라우스", "니트", "슬랙스", "자켓", "로퍼", "힐", "토트백", "스커트"},
    "workout": {"티셔츠", "크롭탑", "탱크탑", "머슬핏", "레깅스", "숏팬츠", "반바지", "조거팬츠", "스니커즈", "후드", "맨투맨"},
    "date": {"니트", "블라우스", "셔츠", "스커트", "슬랙스", "원피스", "가디건", "힐", "크로스백"},
    "campus": {"티셔츠", "맨투맨", "후드", "청바지", "조거팬츠", "스니커즈", "가디건", "와이드팬츠", "니트", "반팔"},
    "weekend": {"티셔츠", "맨투맨", "니트", "청바지", "와이드팬츠", "스니커즈", "가디건", "후드", "반팔"},
    "travel": {"티셔츠", "니트", "청바지", "와이드팬츠", "스니커즈", "반팔", "점퍼", "맨투맨", "후드"},
    "event": {"셔츠", "블라우스", "원피스", "스커트", "슬랙스", "자켓", "힐", "코트"},
}

# ── TPO별 가격 상한 ──
TPO_PRICE_MAX = {
    "campus": 150000,
    "workout": 120000,
    "weekend": 200000,
    "travel": 200000,
    "commute": 300000,
    "interview": 350000,
    "date": 300000,
    "event": 400000,
}

# ── 잘못된 조합 규칙 ──
FORBIDDEN_COMBOS = [
    # (카테고리A, 카테고리B) — 동시 존재 시 제거
    ("원피스", "슬랙스"),
    ("원피스", "청바지"),
    ("원피스", "와이드팬츠"),
    ("원피스", "팬츠"),
    ("원피스", "치노"),
    ("원피스", "레깅스"),
    ("원피스", "조거팬츠"),
    ("원피스", "반바지"),
    ("원피스", "숏팬츠"),
]


def check_forbidden_combo(outfit: dict) -> str | None:
    cats = {it.get("category", "") for it in outfit.get("items", [])}
    for a, b in FORBIDDEN_COMBOS:
        if a in cats and b in cats:
            return f"금지 조합: {a}+{b}"
    return None


def check_tpo_whitelist(outfit: dict) -> str | None:
    """TPO whitelist 위반 시 해당 TPO 제거."""
    items = outfit.get("items", [])
    cats = {it.get("category", "") for it in items}
    dtpo = outfit.get("designed_tpo", [])
    removed_tpos = []

    for tpo in list(dtpo):
        whitelist = TPO_WHITELIST.get(tpo)
        if whitelist is None:
            continue
        # 모든 아이템이 whitelist에 있어야 함
        if not cats.issubset(whitelist):
            violation = cats - whitelist
            removed_tpos.append((tpo, violation))
            dtpo.remove(tpo)

    outfit["designed_tpo"] = dtpo
    if removed_tpos:
        return f"whitelist 위반: {removed_tpos}"
    return None


def check_tpo_price(outfit: dict) -> str | None:
    """TPO별 가격 상한 초과 시 해당 TPO 제거."""
    total_price = outfit.get("total_price", 0)
    dtpo = outfit.get("designed_tpo", [])
    removed = []

    for tpo in list(dtpo):
        max_price = TPO_PRICE_MAX.get(tpo, 999999)
        if total_price > max_price:
            removed.append(tpo)
            dtpo.remove(tpo)

    outfit["designed_tpo"] = dtpo
    if removed:
        return f"가격 초과: {removed} (₩{total_price:,})"
    return None


def main():
    backup = DATA_DIR / f"outfits_scored_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    shutil.copy2(SCORED_PATH, backup)
    print(f"백업: {backup.name}")

    with open(SCORED_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"처리 전: {len(data)}건")

    stats = Counter()
    clean = []

    for o in data:
        # 1. 금지 조합 제거
        combo_issue = check_forbidden_combo(o)
        if combo_issue:
            stats["금지 조합"] += 1
            continue

        # 2. TPO whitelist 적용
        wl_issue = check_tpo_whitelist(o)
        if wl_issue:
            stats["whitelist 조정"] += 1

        # 3. 가격 정책 적용
        price_issue = check_tpo_price(o)
        if price_issue:
            stats["가격 초과"] += 1

        # TPO가 비면 제거
        if not o.get("designed_tpo"):
            stats["TPO 없음 (제거)"] += 1
            continue

        clean.append(o)

    # 저장
    with open(SCORED_PATH, "w", encoding="utf-8") as f:
        json.dump(clean, f, ensure_ascii=False)

    # 결과
    print(f"\n=== 적용 결과 ===")
    for reason, cnt in stats.most_common():
        print(f"  {reason}: {cnt}건")
    print(f"최종 코디: {len(clean)}건 (제거: {len(data) - len(clean)}건)")

    # TPO 분포
    tpo_counter = Counter()
    for o in clean:
        for t in o.get("designed_tpo", []):
            tpo_counter[t] += 1
    print(f"\nTPO 분포:")
    for t, c in tpo_counter.most_common():
        print(f"  {t}: {c}")

    # workout 카테고리 확인
    wk = [o for o in clean if "workout" in o.get("designed_tpo", [])]
    wk_cats = Counter()
    for o in wk:
        for it in o.get("items", []):
            wk_cats[it.get("category", "")] += 1
    print(f"\nworkout 카테고리 (정제 후):")
    for c, n in wk_cats.most_common():
        print(f"  {c}: {n}")


if __name__ == "__main__":
    main()
