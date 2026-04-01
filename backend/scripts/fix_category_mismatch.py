"""
카테고리 오분류 수정 스크립트.

상품명(name)에 포함된 키워드와 현재 category가 불일치하는 경우 수정.
outfits_scored.json을 직접 수정하고 백업을 생성.

사용법:
    cd backend
    python -m scripts.fix_category_mismatch
    python -m scripts.fix_category_mismatch --dry-run   # 수정 없이 검사만
"""

import argparse
import json
import re
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SCORED_PATH = DATA_DIR / "outfits_scored.json"

# ──────────────────────────────────────────────
# 상품명 → 올바른 카테고리 매핑 (우선순위 순)
# ──────────────────────────────────────────────
NAME_TO_CATEGORY_RULES = [
    # (이름에 포함된 키워드, 올바른 카테고리, 잘못 분류될 수 있는 카테고리들)
    (["원피스", "드레스"], "원피스", {"탱크탑", "크롭탑", "티셔츠", "셔츠", "블라우스", "니트", "맨투맨"}),
    (["점프수트"], "점프수트", {"티셔츠", "셔츠", "슬랙스", "팬츠"}),
    (["패딩"], "패딩", {"크롭탑", "탱크탑", "티셔츠", "니트", "셔츠"}),
    (["코트"], "코트", {"크롭탑", "탱크탑", "티셔츠", "니트", "셔츠", "자켓"}),
    (["자켓", "재킷"], "자켓", {"크롭탑", "탱크탑", "티셔츠", "니트", "셔츠"}),
    (["후드"], "후드", {"셔츠", "블라우스", "니트", "슬랙스"}),
    (["맨투맨", "스웨트셔츠"], "맨투맨", {"셔츠", "블라우스", "슬랙스"}),
    (["레깅스"], "레깅스", {"슬랙스", "팬츠", "스커트"}),
    (["조거팬츠", "조거"], "조거팬츠", {"슬랙스", "청바지"}),
]


def detect_correct_category(name: str, current_cat: str) -> str | None:
    """상품명에서 올바른 카테고리를 감지. 변경 필요 없으면 None."""
    name_lower = name.lower()
    for keywords, correct_cat, wrong_cats in NAME_TO_CATEGORY_RULES:
        for kw in keywords:
            if kw in name_lower and current_cat in wrong_cats:
                return correct_cat
    return None



# TPO별 상품명 금지 키워드 (카테고리는 맞지만 상품 자체가 부적합)
TPO_NAME_BLACKLIST: dict[str, list[str]] = {
    "interview": ["후드", "후디", "스웨트", "조거", "트레이닝", "레깅스", "크롭", "캐주얼 반팔", "트랙"],
    "commute": ["후드", "후디", "트레이닝", "조거", "트랙"],
    "workout": ["원피스", "드레스", "블라우스", "코트", "자켓", "패딩"],
}


def check_outfit_validity(outfit: dict) -> list[str]:
    """코디의 카테고리 구성 + 상품명 적합성 검사. 위반 사항 반환."""
    tpo_list = outfit.get("designed_tpo", [])
    items = outfit.get("items", [])
    cats = {it.get("category", "") for it in items}
    issues = []

    for tpo in tpo_list:
        if tpo == "workout":
            if cats & {"원피스", "블라우스", "코트", "자켓", "패딩", "점프수트"}:
                issues.append(f"workout에 금지 카테고리: {cats & {'원피스','블라우스','코트','자켓','패딩','점프수트'}}")
        elif tpo == "interview":
            forbidden = {"후드", "맨투맨", "크롭탑", "탱크탑", "레깅스", "숏팬츠", "패딩", "코트", "조거팬츠"}
            if cats & forbidden:
                issues.append(f"interview에 금지 카테고리: {cats & forbidden}")
        elif tpo == "commute":
            if cats & {"숏팬츠", "레깅스", "크롭탑", "탱크탑"}:
                issues.append(f"commute에 금지 카테고리: {cats & {'숏팬츠','레깅스','크롭탑','탱크탑'}}")

        # 상품명 키워드 블랙리스트 검사
        blacklist = TPO_NAME_BLACKLIST.get(tpo, [])
        if blacklist:
            for it in items:
                name_lower = it.get("name", "").lower()
                for kw in blacklist:
                    if kw in name_lower:
                        issues.append(f"{tpo}에 부적합 상품명: '{kw}' in '{it['name'][:40]}'")
                        break

    return issues


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="수정 없이 검사만")
    args = parser.parse_args()

    with open(SCORED_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"총 코디: {len(data)}")
    total_items = sum(len(o.get("items", [])) for o in data)
    print(f"총 아이템: {total_items}")

    # STEP 1: 카테고리 재분류
    fix_count = 0
    fix_log = []
    for o in data:
        for it in o.get("items", []):
            name = it.get("name", "")
            old_cat = it.get("category", "")
            new_cat = detect_correct_category(name, old_cat)
            if new_cat:
                fix_log.append({
                    "outfit_id": o.get("outfit_id", ""),
                    "old": old_cat,
                    "new": new_cat,
                    "name": name[:60],
                })
                if not args.dry_run:
                    it["category"] = new_cat
                fix_count += 1

    print(f"\n카테고리 수정: {fix_count}건")
    if fix_log:
        print("샘플 (최대 10건):")
        for log in fix_log[:10]:
            print(f"  {log['old']} → {log['new']} | {log['name']}")

    # STEP 2: 코디 정합성 검사 (카테고리 수정 후)
    broken = []
    for o in data:
        issues = check_outfit_validity(o)
        if issues:
            broken.append({
                "outfit_id": o.get("outfit_id", ""),
                "designed_tpo": o.get("designed_tpo", []),
                "categories": [it.get("category", "") for it in o.get("items", [])],
                "issues": issues,
            })

    print(f"\n코디 정합성 위반: {broken_count}건" if (broken_count := len(broken)) else "\n코디 정합성 위반: 0건")
    if broken:
        print("위반 샘플 (최대 10건):")
        for b in broken[:10]:
            print(f"  {b['outfit_id'][:30]} | tpo={b['designed_tpo']} | cats={b['categories']} | {b['issues']}")

    # STEP 3: 위반 코디 제거
    if broken and not args.dry_run:
        broken_ids = {b["outfit_id"] for b in broken}
        before = len(data)
        data = [o for o in data if o.get("outfit_id", "") not in broken_ids]
        removed = before - len(data)
        print(f"\n위반 코디 제거: {removed}건 (남은 코디: {len(data)})")

        # broken 로그 저장
        broken_path = DATA_DIR / "broken_outfits.json"
        with open(broken_path, "w", encoding="utf-8") as f:
            json.dump(broken, f, ensure_ascii=False, indent=2)
        print(f"위반 로그 저장: {broken_path}")

    # STEP 4: 저장
    if not args.dry_run and (fix_count > 0 or broken):
        # 백업
        backup_name = f"outfits_scored_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        backup_path = DATA_DIR / backup_name
        shutil.copy2(SCORED_PATH, backup_path)
        print(f"\n백업: {backup_path.name}")

        # 저장
        with open(SCORED_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        print(f"저장: outfits_scored.json ({len(data)}건)")

    # STEP 5: 최종 통계
    print("\n=== 최종 검증 ===")
    remaining_mismatch = 0
    for o in data:
        for it in o.get("items", []):
            if detect_correct_category(it.get("name", ""), it.get("category", "")):
                remaining_mismatch += 1
    print(f"남은 오분류: {remaining_mismatch}건")

    remaining_broken = sum(1 for o in data if check_outfit_validity(o))
    print(f"남은 정합성 위반: {remaining_broken}건")

    if args.dry_run:
        print("\n[DRY RUN] 실제 수정은 적용되지 않았습니다.")


if __name__ == "__main__":
    main()
