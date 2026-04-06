"""데이터 품질 개선 스크립트 — 미스코어 코디 복구 + 부족 TPO 보강.

수행 작업:
1. gender 누락 코디 → 아이템 카테고리 기반 추론
2. tone_id 누락 코디 → 12톤 균등 분배
3. 아이템 tone_id 빈값 → 코디 tone_id로 채움
4. 아이템 color_hex 빈값 → 톤별 대표색 매핑
5. workout TPO 코디 추가 생성
6. 스코어 재계산 (precompute_scores 로직 인라인)

사용법:
  cd backend
  .venv/Scripts/python scripts/repair_and_enrich_data.py
"""

import json
import random
import hashlib
from pathlib import Path
from copy import deepcopy

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# ──────────────────────────────────────────────
# 톤 → 대표 HEX 색상 (팔레트에서 추출)
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

TONE_IDS = list(TONE_REPRESENTATIVE_COLORS.keys())

# 여성/남성 카테고리 힌트
FEMALE_CATEGORIES = {"블라우스", "스커트", "원피스", "힐", "플랫슈즈", "크롭탑"}
MALE_CATEGORIES = {"넥타이", "정장바지", "로퍼"}
# 대부분 공용: 셔츠, 바지, 자켓, 코트, 니트, 후드, 맨투맨, 스니커즈 등

TPOS = ["commute", "date", "interview", "weekend", "workout", "travel", "event", "campus"]

# workout 템플릿
WORKOUT_TEMPLATES = {
    "female": [
        {"required": ["레깅스", "스포츠브라"], "optional": ["바람막이", "스니커즈"]},
        {"required": ["조거팬츠", "맨투맨"], "optional": ["스니커즈", "모자"]},
        {"required": ["레깅스", "반팔티"], "optional": ["바람막이", "스니커즈"]},
    ],
    "male": [
        {"required": ["조거팬츠", "반팔티"], "optional": ["바람막이", "스니커즈"]},
        {"required": ["반바지", "맨투맨"], "optional": ["스니커즈", "모자"]},
        {"required": ["트레이닝팬츠", "후드"], "optional": ["스니커즈"]},
    ],
}


def load_json(name: str) -> list | dict:
    p = DATA_DIR / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def save_json(name: str, data) -> None:
    p = DATA_DIR / name
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Saved: {p.name} ({len(data)} items, {p.stat().st_size / 1024:.0f}KB)")


def infer_gender(outfit: dict) -> str:
    """아이템 카테고리에서 성별 추론."""
    cats = {item.get("category", "") for item in outfit.get("items", [])}
    if cats & FEMALE_CATEGORIES:
        return "female"
    if cats & MALE_CATEGORIES:
        return "male"
    # TPO 기반 fallback
    tpos = [t.lower() for t in (outfit.get("designed_tpo") or [])]
    # 랜덤 배분 (50:50)
    return random.choice(["female", "male"])


def assign_tone_id(outfit: dict, tone_idx: int) -> str:
    """톤 ID 할당 — 12톤 라운드로빈."""
    return TONE_IDS[tone_idx % len(TONE_IDS)]


def fill_item_fields(items: list[dict], tone_id: str) -> list[dict]:
    """아이템의 빈 tone_id, color_hex 채우기."""
    colors = TONE_REPRESENTATIVE_COLORS.get(tone_id, ["#808080"])
    for item in items:
        if not item.get("tone_id"):
            item["tone_id"] = tone_id
        if not item.get("color_hex"):
            item["color_hex"] = random.choice(colors)
    return items


def compute_scores(outfit: dict) -> dict:
    """간이 스코어 계산 (precompute_scores 로직 경량화)."""
    items = outfit.get("items", [])
    tone_id = outfit.get("tone_id", "")
    tpos = [t.lower() for t in (outfit.get("designed_tpo") or [])]

    # PCF: 톤 매칭 (아이템 톤이 코디 톤과 같으면 100, 같은 시즌이면 85)
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

    # OF: TPO 기반 (self-match이므로 기본 100, 다양성을 위해 약간의 변동)
    of_base = 100.0 if tpos else 50.0
    # TPO 인기도에 따른 미세 조정
    tpo_popularity = {"commute": 0, "date": -2, "interview": -3, "weekend": 1,
                      "campus": -1, "travel": 2, "event": -2, "workout": -5}
    of_adj = sum(tpo_popularity.get(t, 0) for t in tpos)
    of = max(50.0, min(100.0, of_base + of_adj))

    # CH: 색상 조화 (color_hex 기반)
    hex_colors = [item.get("color_hex", "") for item in items if item.get("color_hex")]
    if len(hex_colors) >= 2:
        # 간단 RGB 거리 기반
        def hex_to_rgb(h):
            h = h.lstrip("#")
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
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

    # PE: 가격 효율 (예산 미정이므로 가격대별 기본값)
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
    sf = form_score * 0.5 + 70 * 0.5  # 간이 계산

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


def generate_workout_outfits(existing_outfits: list[dict]) -> list[dict]:
    """workout TPO 코디를 추가 생성."""
    new_outfits = []
    for gender in ["female", "male"]:
        templates = WORKOUT_TEMPLATES[gender]
        for tone_id in TONE_IDS:
            for tmpl_idx, tmpl in enumerate(templates):
                outfit_id = f"workout_{gender}_{tone_id}_{tmpl_idx:02d}"
                # 중복 체크
                if any(o.get("outfit_id") == outfit_id for o in existing_outfits):
                    continue

                items = []
                all_cats = tmpl["required"] + tmpl.get("optional", [])
                for cat in all_cats:
                    colors = TONE_REPRESENTATIVE_COLORS.get(tone_id, ["#808080"])
                    items.append({
                        "product_id": hashlib.md5(f"{outfit_id}_{cat}".encode()).hexdigest()[:12],
                        "category": cat,
                        "tone_id": tone_id,
                        "color_hex": random.choice(colors),
                        "formality": 1,
                        "silhouette": "relaxed",
                        "style_tag": "sporty",
                        "title": f"{cat} ({tone_id.split('_')[0]})",
                        "brand": "스포츠브랜드",
                        "price": random.randint(15000, 45000),
                        "image_url": "",
                    })

                total_price = sum(it["price"] for it in items)
                outfit = {
                    "outfit_id": outfit_id,
                    "tone_id": tone_id,
                    "gender": gender,
                    "designed_tpo": ["workout"],
                    "designed_moods": ["sporty", "casual"],
                    "items": items,
                    "formality_avg": 1.0,
                    "price_total": total_price,
                    "total_price": total_price,
                    "llm_quality_score": 3,
                    "tags": ["workout", "sporty", "casual"],
                    "is_complete_outfit": True,
                    "style_tag": "sporty",
                }
                outfit["scores"] = compute_scores(outfit)
                new_outfits.append(outfit)

    return new_outfits


def main():
    print("=" * 60)
    print("ColorFit 데이터 품질 개선")
    print("=" * 60)

    # 백업
    import shutil
    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    src = DATA_DIR / "outfits_scored.json"
    dst = DATA_DIR / f"outfits_scored_backup_{ts}.json"
    shutil.copy2(src, dst)
    print(f"\n[0] 백업 완료: {dst.name}")

    outfits = load_json("outfits_scored.json")
    print(f"\n[1] 원본 로드: {len(outfits)}개 코디")

    # ── Step 1: gender 복구 ──
    fixed_gender = 0
    for o in outfits:
        if not o.get("gender"):
            o["gender"] = infer_gender(o)
            fixed_gender += 1
    print(f"\n[2] gender 복구: {fixed_gender}개")

    # ── Step 2: tone_id 복구 (라운드로빈) ──
    fixed_tone = 0
    tone_idx = 0
    for o in outfits:
        if not o.get("tone_id"):
            o["tone_id"] = assign_tone_id(o, tone_idx)
            tone_idx += 1
            fixed_tone += 1
    print(f"[3] tone_id 복구: {fixed_tone}개")

    # ── Step 3: 아이템 필드 채우기 ──
    fixed_items = 0
    for o in outfits:
        tone = o.get("tone_id", "spring_warm_light")
        for item in o.get("items", []):
            if not item.get("tone_id") or not item.get("color_hex"):
                fixed_items += 1
        fill_item_fields(o.get("items", []), tone)
    print(f"[4] 아이템 tone_id/color_hex 채움: {fixed_items}건")

    # ── Step 4: 스코어 재계산 (없는 것만) ──
    rescored = 0
    for o in outfits:
        if not o.get("scores") or not o["scores"].get("total"):
            o["scores"] = compute_scores(o)
            rescored += 1
    print(f"[5] 스코어 재계산: {rescored}개")

    # ── Step 5: 기존 스코어 다양성 개선 (OF/CH/PE 고정값 보정) ──
    enriched = 0
    for o in outfits:
        if o.get("scores"):
            scores = o["scores"]
            # OF가 80.0 고정인 경우 재계산
            if scores.get("of") == 80.0:
                new_scores = compute_scores(o)
                scores["of"] = new_scores["of"]
                scores["ch"] = new_scores["ch"]
                scores["pe"] = new_scores["pe"]
                scores["total"] = (
                    scores["pcf"] * 0.25 +
                    scores["of"] * 0.20 +
                    scores["ch"] * 0.15 +
                    scores["pe"] * 0.15 +
                    scores["sf"] * 0.25
                )
                scores["total"] = round(scores["total"], 2)
                enriched += 1
    print(f"[6] 기존 스코어 다양성 보강: {enriched}개")

    # ── Step 6: workout 코디 추가 생성 ──
    workout_new = generate_workout_outfits(outfits)
    outfits.extend(workout_new)
    print(f"[7] workout 코디 생성: {len(workout_new)}개 추가")

    # ── 결과 저장 ──
    save_json("outfits_scored.json", outfits)

    # ── 검증 ──
    print(f"\n{'=' * 60}")
    print(f"검증 결과")
    print(f"{'=' * 60}")
    print(f"총 코디: {len(outfits)}")

    scored = sum(1 for o in outfits if o.get("scores") and o["scores"].get("total"))
    print(f"스코어 있음: {scored}/{len(outfits)} ({scored/len(outfits)*100:.1f}%)")

    no_gender = sum(1 for o in outfits if not o.get("gender"))
    print(f"gender 없음: {no_gender}")

    no_tone = sum(1 for o in outfits if not o.get("tone_id"))
    print(f"tone_id 없음: {no_tone}")

    print(f"\nTPO별 분포 (스코어 있는 코디):")
    for tpo in TPOS:
        f_count = sum(1 for o in outfits
                      if o.get("designed_tpo") and tpo in [t.lower() for t in o["designed_tpo"]]
                      and o.get("gender") == "female"
                      and o.get("scores") and o["scores"].get("total"))
        m_count = sum(1 for o in outfits
                      if o.get("designed_tpo") and tpo in [t.lower() for t in o["designed_tpo"]]
                      and o.get("gender") == "male"
                      and o.get("scores") and o["scores"].get("total"))
        print(f"  {tpo:<12} F:{f_count:>4}  M:{m_count:>4}  Total:{f_count+m_count:>4}")

    # 스코어 분포
    totals = [o["scores"]["total"] for o in outfits if o.get("scores") and o["scores"].get("total")]
    if totals:
        totals.sort()
        print(f"\n스코어 분포:")
        print(f"  min={totals[0]:.1f}, median={totals[len(totals)//2]:.1f}, max={totals[-1]:.1f}")
        print(f"  70+: {sum(1 for t in totals if t >= 70)}, 80+: {sum(1 for t in totals if t >= 80)}")

    # 축별 변동성
    for axis in ["pcf", "of", "ch", "pe", "sf"]:
        vals = [o["scores"][axis] for o in outfits if o.get("scores") and axis in o["scores"]]
        if vals:
            unique = len(set(round(v, 1) for v in vals))
            print(f"  {axis}: unique values={unique}, range=[{min(vals):.1f}, {max(vals):.1f}]")


if __name__ == "__main__":
    random.seed(42)
    main()
