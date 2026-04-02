"""
데이터 품질 검증 스크립트.

사용법:
    cd backend
    python -m scripts.verify_data_quality
"""

import json
import math
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SCORED_PATH = DATA_DIR / "outfits_scored.json"


def main():
    with open(SCORED_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_items = 0
    color_filled = 0
    season_tagged = 0
    tpo_counter = Counter()
    gender_counter = Counter()
    totals = []
    axis_scores = {"pcf": [], "of": [], "ch": [], "pe": [], "sf": []}
    expensive = []

    for o in data:
        items = o.get("items", [])
        for it in items:
            total_items += 1
            h = it.get("color_hex", "")
            if h and h != "" and h != "#808080":
                color_filled += 1

        tags = set(o.get("tags", []))
        if tags & {"spring", "summer", "autumn", "winter"}:
            season_tagged += 1

        for t in o.get("designed_tpo", []):
            tpo_counter[t] += 1

        oid = o.get("outfit_id", "")
        if "female" in oid:
            gender_counter["female"] += 1
        elif "male" in oid:
            gender_counter["male"] += 1

        scores = o.get("scores", {})
        if scores.get("total"):
            totals.append(scores["total"])
        for axis in axis_scores:
            if axis in scores:
                axis_scores[axis].append(scores[axis])

        price = o.get("total_price", 0)
        if price >= 7000000:
            expensive.append(f"{oid[:30]}: {price:,}원")

    def stdev(vals):
        if len(vals) < 2:
            return 0
        mean = sum(vals) / len(vals)
        return math.sqrt(sum((v - mean) ** 2 for v in vals) / len(vals))

    # 결과 출력
    print("=" * 60)
    print("ColorFit 데이터 품질 검증")
    print("=" * 60)

    checks = []

    # 1. color_hex
    pct = color_filled / total_items * 100 if total_items else 0
    status = "PASS" if pct >= 90 else "WARN" if pct >= 70 else "FAIL"
    checks.append((status, f"color_hex 채워진 비율: {color_filled}/{total_items} ({pct:.1f}%) [목표: 90%+]"))

    # 2. 시즌 태그
    pct2 = season_tagged / len(data) * 100 if data else 0
    status2 = "PASS" if pct2 >= 95 else "FAIL"
    checks.append((status2, f"시즌 태그 비율: {season_tagged}/{len(data)} ({pct2:.1f}%) [목표: 100%]"))

    # 3. TPO workout
    wk = tpo_counter.get("workout", 0)
    status3 = "PASS" if wk >= 50 else "FAIL"
    checks.append((status3, f"workout 코디 수: {wk} [목표: 50+]"))

    # 4. 총점 분포
    if totals:
        sd = stdev(totals)
        status4 = "PASS" if sd > 5 else "FAIL"
        checks.append((status4, f"총점 stdev: {sd:.2f} [목표: >5] (min={min(totals):.1f}, max={max(totals):.1f}, mean={sum(totals)/len(totals):.1f})"))
    else:
        checks.append(("FAIL", "총점 데이터 없음"))

    # 5. 축별 stdev
    for axis in ["pcf", "of", "ch", "pe", "sf"]:
        vals = axis_scores[axis]
        if vals:
            sd = stdev(vals)
            s = "PASS" if sd > 3 else "WARN"
            checks.append((s, f"{axis} stdev: {sd:.2f} (min={min(vals):.1f}, max={max(vals):.1f})"))

    # 6. 성별 비율
    checks.append(("INFO", f"성별: female={gender_counter.get('female',0)}, male={gender_counter.get('male',0)}"))

    # 7. 가격 극단값
    if expensive:
        checks.append(("WARN", f"700만원+ 코디: {len(expensive)}건"))
    else:
        checks.append(("PASS", "700만원+ 코디: 0건"))

    # TPO 분포
    checks.append(("INFO", f"TPO 분포: {dict(tpo_counter.most_common())}"))

    for status, msg in checks:
        icon = "✅" if status == "PASS" else "⚠️" if status == "WARN" else "❌" if status == "FAIL" else "ℹ️"
        print(f"  {icon} [{status}] {msg}")

    print(f"\n총 코디: {len(data)}")
    print(f"총 아이템: {total_items}")


if __name__ == "__main__":
    main()
