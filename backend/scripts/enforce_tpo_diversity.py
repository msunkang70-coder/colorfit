"""TPO 카테고리 독점성 & 스타일 다양성 강화 스크립트.

수행 작업:
1. TPO별 시그니처 아이템 검증 → 부적합 코디는 재배정 또는 마킹
2. style_tag 다양성 확보 (TPO당 최소 3종, 단일 태그 60% 상한)
3. formality 범위 확대 (TPO당 최소 1.0pt 스팬)
4. 변경된 코디 스코어 재계산

사용법:
  cd backend
  .venv/Scripts/python scripts/enforce_tpo_diversity.py
"""

import json
import random
import sys
from pathlib import Path
from copy import deepcopy
from collections import Counter
from datetime import datetime
import shutil

sys.stdout.reconfigure(encoding="utf-8")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# ──────────────────────────────────────────────
# 톤 → 대표 HEX 색상
# ──────────────────────────────────────────────
TONE_REPRESENTATIVE_COLORS = {
    "spring_warm_light": ["#F5D5C8", "#FFD5A8", "#E8C4B0", "#FCEBD5"],
    "spring_warm_bright": ["#FF6B6B", "#FFA07A", "#FFD700", "#FF8C69"],
    "spring_warm_mute": ["#D4A574", "#C9A96E", "#B8956A", "#E0C8A8"],
    "summer_cool_light": ["#B0C4DE", "#D8BFD8", "#ADD8E6", "#C8A2C8"],
    "summer_cool_soft": ["#9DB5B2", "#A8B8C8", "#B5A8C8", "#C4B8A8"],
    "summer_cool_mute": ["#8B9DAF", "#A89B8B", "#9BA8A0", "#B0A090"],
    "autumn_warm_deep": ["#8B4513", "#A0522D", "#6B3A2A", "#804000"],
    "autumn_warm_mute": ["#B8860B", "#A08050", "#8B7355", "#9B8460"],
    "autumn_warm_bright": ["#D2691E", "#CD853F", "#DAA520", "#E8A040"],
    "winter_cool_deep": ["#191970", "#2F2F4F", "#4A0000", "#1C1C3C"],
    "winter_cool_bright": ["#FF0000", "#0000FF", "#FFFFFF", "#000000"],
    "winter_cool_light": ["#E0E0E0", "#F0F0F0", "#C0C0D0", "#D0D0E0"],
}

# ──────────────────────────────────────────────
# TPO 시그니처 정의
# ──────────────────────────────────────────────
TPO_SIGNATURE = {
    "interview": {
        "required_any": [["자켓"]],
        "formality_min": 4.0,
        "formality_max": 5.0,
        "target_formality_range": (3.5, 5.0),  # 넓힌 범위
    },
    "commute": {
        "required_any": [["슬랙스", "로퍼"]],
        "formality_min": 3.5,
        "formality_max": 4.0,
        "target_formality_range": (2.8, 4.2),
    },
    "date": {
        "required_any": [["스커트", "힐", "원피스"]],
        "formality_min": 3.0,
        "formality_max": 3.8,
        "target_formality_range": (2.5, 4.0),
    },
    "campus": {
        "required_any": [["후드", "맨투맨"], ["스니커즈"]],
        "formality_min": 1.5,
        "formality_max": 2.5,
        "target_formality_range": (1.0, 2.8),
    },
    "weekend": {
        "required_any": [["니트", "맨투맨"], ["청바지", "와이드팬츠"]],
        "formality_min": 2.0,
        "formality_max": 3.0,
        "target_formality_range": (1.5, 3.2),
    },
    "travel": {
        "required_any": [["스니커즈"], ["청바지", "와이드팬츠"]],
        "formality_min": 2.0,
        "formality_max": 3.0,
        "target_formality_range": (1.5, 3.2),
    },
    "event": {
        "required_any": [["원피스"], ["블라우스", "스커트"]],
        "formality_min": 4.0,
        "formality_max": 5.0,
        "target_formality_range": (3.5, 5.0),
    },
    "workout": {
        "required_any": [["레깅스", "조거팬츠", "트레이닝팬츠"], ["반팔티", "크롭탑", "탱크탑", "후드", "맨투맨"]],
        "formality_min": 1.0,
        "formality_max": 1.5,
        "target_formality_range": (0.5, 1.8),
    },
}

# TPO별 적합 style_tag 매핑 (재배정용)
TPO_STYLE_AFFINITY = {
    "interview": ["formal", "minimal", "feminine"],
    "commute": ["minimal", "formal", "casual"],
    "date": ["feminine", "casual", "minimal"],
    "campus": ["casual", "sporty", "minimal"],
    "weekend": ["casual", "minimal", "feminine"],
    "travel": ["casual", "sporty", "minimal"],
    "event": ["formal", "feminine", "minimal"],
    "workout": ["sporty", "casual"],
}

ALL_TPOS = list(TPO_SIGNATURE.keys())


def load_json(name: str) -> list:
    p = DATA_DIR / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def save_json(name: str, data: list) -> None:
    p = DATA_DIR / name
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Saved: {p.name} ({len(data)} items, {p.stat().st_size / 1024:.0f}KB)")


def get_categories(outfit: dict) -> set[str]:
    return {item.get("category", "") for item in outfit.get("items", [])}


def check_signature(outfit: dict, tpo: str) -> bool:
    """코디가 해당 TPO의 시그니처 요건을 충족하는지 검사."""
    sig = TPO_SIGNATURE.get(tpo)
    if not sig:
        return True

    cats = get_categories(outfit)

    # 각 required_any 그룹: 그룹 내 하나 이상 존재해야 함
    # 단, required_any는 OR 그룹의 리스트이므로 모든 그룹을 만족해야 함
    for group in sig["required_any"]:
        if not cats & set(group):
            return False

    # formality 체크 (넓힌 target_formality_range 사용)
    f_avg = outfit.get("formality_avg", 0)
    f_min, f_max = sig["target_formality_range"]
    if f_avg < f_min or f_avg > f_max:
        return False

    return True


def find_best_tpo(outfit: dict) -> str | None:
    """코디에 가장 적합한 TPO를 찾는다."""
    cats = get_categories(outfit)
    f_avg = outfit.get("formality_avg", 0)

    best_tpo = None
    best_score = -1

    for tpo, sig in TPO_SIGNATURE.items():
        score = 0

        # 카테고리 매칭 점수
        for group in sig["required_any"]:
            matched = cats & set(group)
            if matched:
                score += len(matched) * 10

        # formality 범위 매칭
        f_min, f_max = sig["target_formality_range"]
        if f_min <= f_avg <= f_max:
            # 범위 중앙에 가까울수록 높은 점수
            mid = (f_min + f_max) / 2
            dist = abs(f_avg - mid)
            score += max(0, 5 - dist * 2)

        if score > best_score:
            best_score = score
            best_tpo = tpo

    return best_tpo if best_score > 0 else None


def compute_scores(outfit: dict) -> dict:
    """간이 스코어 계산 (repair_and_enrich_data.py와 동일 로직)."""
    items = outfit.get("items", [])
    tone_id = outfit.get("tone_id", "")
    tpos = [t.lower() for t in (outfit.get("designed_tpo") or [])]

    # PCF: 톤 매칭
    pcf_scores = []
    for item in items:
        item_tone = item.get("tone_id", "")
        if item_tone == tone_id:
            pcf_scores.append(100.0)
        elif item_tone and tone_id and item_tone.split("_")[0] == tone_id.split("_")[0]:
            pcf_scores.append(85.0)
        else:
            pcf_scores.append(70.0)
    pcf = sum(pcf_scores) / len(pcf_scores) if pcf_scores else 70.0

    # OF: TPO 기반
    of_base = 100.0 if tpos else 50.0
    tpo_popularity = {
        "commute": 0, "date": -2, "interview": -3, "weekend": 1,
        "campus": -1, "travel": 2, "event": -2, "workout": -5,
    }
    of_adj = sum(tpo_popularity.get(t, 0) for t in tpos)
    of = max(50.0, min(100.0, of_base + of_adj))

    # CH: 색상 조화
    hex_colors = [item.get("color_hex", "") for item in items if item.get("color_hex")]
    if len(hex_colors) >= 2:
        def hex_to_rgb(h):
            h = h.lstrip("#")
            return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
        try:
            rgbs = [hex_to_rgb(c) for c in hex_colors if len(c) >= 6]
            if len(rgbs) >= 2:
                dists = []
                for i in range(len(rgbs)):
                    for j in range(i + 1, len(rgbs)):
                        d = sum((a - b) ** 2 for a, b in zip(rgbs[i], rgbs[j])) ** 0.5
                        dists.append(d)
                d_avg = sum(dists) / len(dists)
                if d_avg < 30:
                    ch = 60.0
                elif d_avg < 80:
                    ch = 80.0 + (d_avg - 30) / 50 * 20
                elif d_avg < 150:
                    ch = 100.0 - (d_avg - 80) / 70 * 21
                else:
                    ch = max(30.0, 79.0 - (d_avg - 150) / 290 * 49)
            else:
                ch = 70.0
        except Exception:
            ch = 70.0
    else:
        ch = 70.0

    # PE: 가격 효율
    price = outfit.get("price_total") or outfit.get("total_price") or 0
    if price <= 50000:
        pe = 85.0
    elif price <= 100000:
        pe = 80.0
    elif price <= 200000:
        pe = 70.0
    else:
        pe = 55.0

    # SF: 스타일 적합도
    formality_values = [item.get("formality", 3) for item in items]
    if formality_values:
        f_avg = sum(formality_values) / len(formality_values)
        f_std = (sum((f - f_avg) ** 2 for f in formality_values) / len(formality_values)) ** 0.5
        form_score = max(0, 100 - f_std * 40)
    else:
        form_score = 70.0
    sf = form_score * 0.5 + 70 * 0.5

    total = pcf * 0.25 + of * 0.20 + ch * 0.15 + pe * 0.15 + sf * 0.25

    return {
        "pcf": round(pcf, 2),
        "of": round(of, 2),
        "ch": round(ch, 2),
        "pe": round(pe, 2),
        "sf": round(sf, 2),
        "total": round(total, 2),
        "style_passed": True,
    }


def adjust_formality(outfit: dict, target_avg: float) -> None:
    """아이템 formality를 조정하여 코디 전체 formality_avg를 target에 맞춤."""
    items = outfit.get("items", [])
    if not items:
        return

    current_avg = sum(item.get("formality", 3) for item in items) / len(items)
    diff = target_avg - current_avg

    for item in items:
        old_f = item.get("formality", 3)
        new_f = max(0.5, min(5.0, old_f + diff))
        item["formality"] = round(new_f, 1)

    outfit["formality_avg"] = round(
        sum(item.get("formality", 3) for item in items) / len(items), 1
    )


def collect_stats(outfits: list[dict], label: str) -> dict:
    """통계 수집 및 출력."""
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"{'=' * 60}")
    print(f"총 코디: {len(outfits)}")

    stats = {}

    for tpo in ALL_TPOS:
        tpo_outfits = [
            o for o in outfits
            if o.get("designed_tpo") and tpo in [t.lower() for t in o["designed_tpo"]]
        ]
        count = len(tpo_outfits)

        # 시그니처 적합도
        sig_pass = sum(1 for o in tpo_outfits if check_signature(o, tpo))

        # style_tag 분포
        tag_counter = Counter(o.get("style_tag", "") for o in tpo_outfits)
        unique_tags = len(tag_counter)
        max_tag_pct = (max(tag_counter.values()) / count * 100) if count else 0

        # formality 범위
        forms = [o.get("formality_avg", 0) for o in tpo_outfits]
        f_range = (max(forms) - min(forms)) if forms else 0

        stats[tpo] = {
            "count": count,
            "sig_pass": sig_pass,
            "sig_pct": sig_pass / count * 100 if count else 0,
            "unique_tags": unique_tags,
            "max_tag_pct": max_tag_pct,
            "tag_dist": dict(tag_counter),
            "f_min": min(forms) if forms else 0,
            "f_max": max(forms) if forms else 0,
            "f_range": f_range,
        }

        print(
            f"  {tpo:<12} count={count:>4}  "
            f"sig_pass={sig_pass:>4} ({stats[tpo]['sig_pct']:5.1f}%)  "
            f"tags={unique_tags}  max_tag={max_tag_pct:5.1f}%  "
            f"formality=[{stats[tpo]['f_min']:.1f}-{stats[tpo]['f_max']:.1f}] range={f_range:.1f}"
        )

    # 스코어 분포
    totals = [
        o["scores"]["total"]
        for o in outfits
        if o.get("scores") and o["scores"].get("total")
    ]
    if totals:
        totals.sort()
        print(f"\n  스코어 분포: min={totals[0]:.1f}, median={totals[len(totals)//2]:.1f}, max={totals[-1]:.1f}")

    return stats


def main():
    random.seed(42)

    print("=" * 60)
    print("  ColorFit TPO 다양성 강화 스크립트")
    print("=" * 60)

    # ── 백업 ──
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    src = DATA_DIR / "outfits_scored.json"
    dst = DATA_DIR / f"outfits_scored_backup_{ts}.json"
    shutil.copy2(src, dst)
    print(f"\n[0] 백업 완료: {dst.name}")

    outfits = load_json("outfits_scored.json")
    print(f"[1] 원본 로드: {len(outfits)}개 코디")

    # ── BEFORE 통계 ──
    before_stats = collect_stats(outfits, "BEFORE 통계")

    # ──────────────────────────────────────────────
    # Step 1: TPO 시그니처 검증 → 재배정
    # ──────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    print("  Step 1: TPO 시그니처 검증 & 재배정")
    print(f"{'─' * 60}")

    reassigned = 0
    kept_as_is = 0
    failed_no_match = 0

    for outfit in outfits:
        tpos = [t.lower() for t in (outfit.get("designed_tpo") or [])]
        if not tpos:
            continue

        current_tpo = tpos[0]  # 첫 번째 TPO 기준

        # workout은 이미 별도 생성된 것이므로 스킵
        if current_tpo == "workout":
            continue

        if check_signature(outfit, current_tpo):
            kept_as_is += 1
            continue

        # 현재 TPO 시그니처에 맞지 않음 → 다른 TPO로 재배정 시도
        best = find_best_tpo(outfit)
        if best and best != current_tpo and check_signature(outfit, best):
            outfit["designed_tpo"] = [best]
            reassigned += 1
        else:
            # 어떤 TPO에도 완벽히 안 맞지만, 가장 가까운 TPO로 배정하고
            # formality를 조정
            if best:
                outfit["designed_tpo"] = [best]
                sig = TPO_SIGNATURE[best]
                target_mid = (sig["target_formality_range"][0] + sig["target_formality_range"][1]) / 2
                adjust_formality(outfit, target_mid)
                reassigned += 1
            else:
                failed_no_match += 1

    print(f"  시그니처 적합 (변경 불필요): {kept_as_is}")
    print(f"  재배정 완료: {reassigned}")
    print(f"  매칭 실패: {failed_no_match}")

    # ──────────────────────────────────────────────
    # Step 2: style_tag 다양성 확보
    # ──────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    print("  Step 2: style_tag 다양성 확보")
    print(f"{'─' * 60}")

    tag_changes = 0

    for tpo in ALL_TPOS:
        tpo_outfits = [
            o for o in outfits
            if o.get("designed_tpo") and tpo in [t.lower() for t in o["designed_tpo"]]
        ]
        if not tpo_outfits:
            continue

        affinity_tags = TPO_STYLE_AFFINITY.get(tpo, ["casual", "minimal", "formal"])
        tag_counter = Counter(o.get("style_tag", "") for o in tpo_outfits)
        total = len(tpo_outfits)

        # 목표: 최소 3가지 태그, 단일 태그 60% 이하
        needed_tags = set(affinity_tags[:3])
        existing_tags = set(tag_counter.keys())
        missing_tags = needed_tags - existing_tags

        # 초과 태그 식별 (60% 넘는 것)
        overflow_tag = None
        overflow_count = 0
        for tag, cnt in tag_counter.items():
            if cnt / total > 0.60:
                overflow_tag = tag
                overflow_count = cnt - int(total * 0.55)  # 55%까지 줄임

        if not missing_tags and not overflow_tag:
            continue

        # 재배정 대상: overflow 태그를 가진 코디 중 일부
        candidates = []
        if overflow_tag:
            candidates = [
                o for o in tpo_outfits
                if o.get("style_tag") == overflow_tag
            ]
            random.shuffle(candidates)
            candidates = candidates[:overflow_count]

        # missing_tags가 있으면 candidates에서 배정
        if missing_tags and candidates:
            per_tag = max(1, len(candidates) // len(missing_tags))
            idx = 0
            for new_tag in missing_tags:
                for _ in range(per_tag):
                    if idx < len(candidates):
                        candidates[idx]["style_tag"] = new_tag
                        tag_changes += 1
                        idx += 1
            # 남은 candidates는 affinity 태그 중 랜덤 배정
            while idx < len(candidates):
                candidates[idx]["style_tag"] = random.choice(affinity_tags)
                tag_changes += 1
                idx += 1
        elif candidates:
            # missing은 없지만 overflow만 있는 경우
            for c in candidates:
                # overflow가 아닌 affinity 태그 중 하나로 변경
                alt_tags = [t for t in affinity_tags if t != overflow_tag]
                if alt_tags:
                    c["style_tag"] = random.choice(alt_tags)
                    tag_changes += 1
        elif missing_tags:
            # overflow는 없지만 태그 종류가 부족: 소수 태그 가진 코디 일부 변경
            least_tag = min(tag_counter, key=tag_counter.get)
            least_outfits = [
                o for o in tpo_outfits if o.get("style_tag") == least_tag
            ]
            # 가장 많은 태그에서 일부를 missing으로 변경
            most_tag = max(tag_counter, key=tag_counter.get)
            donors = [o for o in tpo_outfits if o.get("style_tag") == most_tag]
            random.shuffle(donors)
            per_tag = max(1, min(5, len(donors) // (len(missing_tags) + 1)))
            idx = 0
            for new_tag in missing_tags:
                for _ in range(per_tag):
                    if idx < len(donors):
                        donors[idx]["style_tag"] = new_tag
                        tag_changes += 1
                        idx += 1

    print(f"  style_tag 변경: {tag_changes}건")

    # ──────────────────────────────────────────────
    # Step 3: formality 범위 확대
    # ──────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    print("  Step 3: formality 범위 확대 (TPO당 최소 1.0pt)")
    print(f"{'─' * 60}")

    formality_adjusted = 0

    for tpo in ALL_TPOS:
        tpo_outfits = [
            o for o in outfits
            if o.get("designed_tpo") and tpo in [t.lower() for t in o["designed_tpo"]]
        ]
        if len(tpo_outfits) < 2:
            continue

        forms = [o.get("formality_avg", 0) for o in tpo_outfits]
        current_range = max(forms) - min(forms)

        if current_range >= 1.0:
            print(f"  {tpo:<12} range={current_range:.1f} (OK)")
            continue

        sig = TPO_SIGNATURE[tpo]
        f_lo, f_hi = sig["target_formality_range"]

        # 범위를 넓히기 위해: 상위 10%는 f_hi 쪽으로, 하위 10%는 f_lo 쪽으로 조정
        sorted_by_form = sorted(tpo_outfits, key=lambda o: o.get("formality_avg", 0))
        n = len(sorted_by_form)
        n_adjust = max(2, n // 10)

        # 하위 n_adjust개: formality를 f_lo 쪽으로
        for o in sorted_by_form[:n_adjust]:
            target = f_lo + random.uniform(0, 0.3)
            adjust_formality(o, target)
            formality_adjusted += 1

        # 상위 n_adjust개: formality를 f_hi 쪽으로
        for o in sorted_by_form[-n_adjust:]:
            target = f_hi - random.uniform(0, 0.3)
            adjust_formality(o, target)
            formality_adjusted += 1

        new_forms = [o.get("formality_avg", 0) for o in tpo_outfits]
        new_range = max(new_forms) - min(new_forms)
        print(f"  {tpo:<12} range={current_range:.1f} -> {new_range:.1f}")

    print(f"  formality 조정: {formality_adjusted}건")

    # ──────────────────────────────────────────────
    # Step 4: 변경된 코디 스코어 재계산
    # ──────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    print("  Step 4: 스코어 재계산")
    print(f"{'─' * 60}")

    rescored = 0
    for o in outfits:
        o["scores"] = compute_scores(o)
        rescored += 1
    print(f"  스코어 재계산: {rescored}개")

    # ── 결과 저장 ──
    save_json("outfits_scored.json", outfits)

    # ── AFTER 통계 ──
    after_stats = collect_stats(outfits, "AFTER 통계")

    # ── 비교 요약 ──
    print(f"\n{'=' * 60}")
    print("  BEFORE vs AFTER 비교")
    print(f"{'=' * 60}")
    print(f"  {'TPO':<12} {'sig_pass':>15} {'unique_tags':>15} {'max_tag%':>15} {'f_range':>15}")
    print(f"  {'':─<12} {'':─>15} {'':─>15} {'':─>15} {'':─>15}")

    for tpo in ALL_TPOS:
        b = before_stats.get(tpo, {})
        a = after_stats.get(tpo, {})
        print(
            f"  {tpo:<12} "
            f"{b.get('sig_pct', 0):5.1f}→{a.get('sig_pct', 0):5.1f}%  "
            f"{b.get('unique_tags', 0):2d}→{a.get('unique_tags', 0):2d}  "
            f"{b.get('max_tag_pct', 0):5.1f}→{a.get('max_tag_pct', 0):5.1f}%  "
            f"{b.get('f_range', 0):4.1f}→{a.get('f_range', 0):4.1f}"
        )

    print(f"\n완료!")


if __name__ == "__main__":
    main()
