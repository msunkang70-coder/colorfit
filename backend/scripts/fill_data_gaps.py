"""데이터 갭 보충 스크립트 — TPO×성별×톤 조합별 최소 5개 보장.

문제:
  - event+male = 0 (여성전용 시그니처)
  - date+male, campus+male, travel+male 부족
  - 75개 조합이 1-4개 (5개 미만)

해결:
  1. 남성용 TPO 시그니처 재정의
  2. 5개 미만 조합에 부족분 생성
  3. compute_scores로 스코어 계산
  4. outfits_scored.json에 저장 (백업 후)

사용법:
  cd backend
  .venv/Scripts/python scripts/fill_data_gaps.py
"""

import json
import random
import hashlib
from pathlib import Path
from copy import deepcopy
from collections import defaultdict
from datetime import datetime
import shutil

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

TONE_IDS = list(TONE_REPRESENTATIVE_COLORS.keys())

TPOS = ["commute", "date", "interview", "weekend", "workout", "travel", "event", "campus"]

MIN_COUNT = 5  # 조합당 최소 코디 수

# ──────────────────────────────────────────────
# TPO × 성별 시그니처 (카테고리 템플릿)
# ──────────────────────────────────────────────
TPO_SIGNATURES = {
    # event
    ("event", "male"): {
        "templates": [
            {"cats": ["셔츠", "슬랙스", "자켓"], "formality": [4.0, 4.0, 4.5]},
            {"cats": ["셔츠", "슬랙스", "자켓", "로퍼"], "formality": [4.0, 4.0, 4.5, 4.0]},
            {"cats": ["셔츠", "정장바지", "자켓"], "formality": [4.0, 4.5, 4.5]},
        ],
        "moods": ["classic", "formal"],
        "style_tag": "formal",
        "formality_range": (4.0, 4.5),
    },
    ("event", "female"): {
        "templates": [
            {"cats": ["원피스", "힐"], "formality": [4.0, 4.0]},
            {"cats": ["블라우스", "스커트", "힐"], "formality": [4.0, 3.5, 4.0]},
            {"cats": ["원피스", "자켓", "힐"], "formality": [4.0, 4.5, 4.0]},
        ],
        "moods": ["elegant", "feminine"],
        "style_tag": "feminine",
        "formality_range": (3.5, 4.5),
    },
    # date
    ("date", "male"): {
        "templates": [
            {"cats": ["셔츠", "슬랙스", "로퍼"], "formality": [3.5, 3.5, 3.5]},
            {"cats": ["니트", "슬랙스", "로퍼"], "formality": [3.0, 3.5, 3.5]},
            {"cats": ["셔츠", "슬랙스"], "formality": [3.5, 3.5]},
            {"cats": ["니트", "슬랙스", "스니커즈"], "formality": [3.0, 3.5, 2.5]},
        ],
        "moods": ["minimal", "classic"],
        "style_tag": "minimal",
        "formality_range": (3.0, 3.8),
    },
    ("date", "female"): {
        "templates": [
            {"cats": ["블라우스", "스커트", "힐"], "formality": [3.5, 3.0, 3.5]},
            {"cats": ["원피스", "힐"], "formality": [3.5, 3.5]},
            {"cats": ["니트", "스커트", "플랫슈즈"], "formality": [3.0, 3.0, 2.5]},
        ],
        "moods": ["feminine", "romantic"],
        "style_tag": "feminine",
        "formality_range": (2.5, 3.8),
    },
    # campus
    ("campus", "male"): {
        "templates": [
            {"cats": ["후드", "청바지", "스니커즈"], "formality": [1.5, 2.0, 2.0]},
            {"cats": ["맨투맨", "청바지", "스니커즈"], "formality": [2.0, 2.0, 2.0]},
            {"cats": ["맨투맨", "청바지"], "formality": [2.0, 2.0]},
            {"cats": ["후드", "조거팬츠", "스니커즈"], "formality": [1.5, 1.5, 2.0]},
        ],
        "moods": ["casual", "street"],
        "style_tag": "casual",
        "formality_range": (1.5, 2.5),
    },
    ("campus", "female"): {
        "templates": [
            {"cats": ["맨투맨", "스커트", "스니커즈"], "formality": [2.0, 2.5, 2.0]},
            {"cats": ["후드", "청바지", "스니커즈"], "formality": [1.5, 2.0, 2.0]},
            {"cats": ["크롭탑", "청바지", "스니커즈"], "formality": [2.0, 2.0, 2.0]},
        ],
        "moods": ["casual", "street"],
        "style_tag": "casual",
        "formality_range": (1.5, 2.5),
    },
    # travel
    ("travel", "male"): {
        "templates": [
            {"cats": ["티셔츠", "청바지", "스니커즈"], "formality": [2.0, 2.0, 2.0]},
            {"cats": ["맨투맨", "조거팬츠", "스니커즈"], "formality": [2.0, 2.0, 2.0]},
            {"cats": ["티셔츠", "반바지", "스니커즈"], "formality": [2.0, 1.5, 2.0]},
            {"cats": ["맨투맨", "청바지", "스니커즈"], "formality": [2.0, 2.0, 2.0]},
        ],
        "moods": ["casual", "comfortable"],
        "style_tag": "casual",
        "formality_range": (2.0, 3.0),
    },
    ("travel", "female"): {
        "templates": [
            {"cats": ["티셔츠", "청바지", "스니커즈"], "formality": [2.0, 2.0, 2.0]},
            {"cats": ["원피스", "스니커즈"], "formality": [2.5, 2.0]},
            {"cats": ["블라우스", "슬랙스", "플랫슈즈"], "formality": [3.0, 3.0, 2.5]},
        ],
        "moods": ["casual", "comfortable"],
        "style_tag": "casual",
        "formality_range": (2.0, 3.0),
    },
    # commute
    ("commute", "male"): {
        "templates": [
            {"cats": ["셔츠", "슬랙스", "로퍼"], "formality": [3.5, 3.5, 3.5]},
            {"cats": ["셔츠", "슬랙스", "자켓"], "formality": [3.5, 3.5, 4.0]},
            {"cats": ["니트", "슬랙스"], "formality": [3.0, 3.5]},
        ],
        "moods": ["minimal", "classic"],
        "style_tag": "minimal",
        "formality_range": (3.0, 4.0),
    },
    ("commute", "female"): {
        "templates": [
            {"cats": ["블라우스", "슬랙스", "플랫슈즈"], "formality": [3.5, 3.5, 3.0]},
            {"cats": ["셔츠", "슬랙스", "자켓"], "formality": [3.5, 3.5, 4.0]},
            {"cats": ["니트", "스커트", "힐"], "formality": [3.0, 3.0, 3.5]},
        ],
        "moods": ["minimal", "classic"],
        "style_tag": "minimal",
        "formality_range": (3.0, 4.0),
    },
    # interview
    ("interview", "male"): {
        "templates": [
            {"cats": ["셔츠", "정장바지", "자켓", "로퍼"], "formality": [4.5, 4.5, 4.5, 4.0]},
            {"cats": ["셔츠", "슬랙스", "자켓"], "formality": [4.0, 4.0, 4.5]},
            {"cats": ["셔츠", "정장바지", "자켓", "넥타이"], "formality": [4.5, 4.5, 4.5, 5.0]},
        ],
        "moods": ["classic", "formal"],
        "style_tag": "formal",
        "formality_range": (4.0, 5.0),
    },
    ("interview", "female"): {
        "templates": [
            {"cats": ["블라우스", "슬랙스", "자켓", "힐"], "formality": [4.0, 4.0, 4.5, 4.0]},
            {"cats": ["셔츠", "스커트", "자켓"], "formality": [4.0, 3.5, 4.5]},
            {"cats": ["블라우스", "슬랙스", "자켓"], "formality": [4.0, 4.0, 4.5]},
        ],
        "moods": ["classic", "formal"],
        "style_tag": "formal",
        "formality_range": (3.5, 5.0),
    },
    # weekend
    ("weekend", "male"): {
        "templates": [
            {"cats": ["티셔츠", "청바지", "스니커즈"], "formality": [2.0, 2.0, 2.0]},
            {"cats": ["맨투맨", "청바지", "스니커즈"], "formality": [2.0, 2.0, 2.0]},
            {"cats": ["후드", "조거팬츠", "스니커즈"], "formality": [1.5, 1.5, 2.0]},
        ],
        "moods": ["casual", "relaxed"],
        "style_tag": "casual",
        "formality_range": (1.5, 2.5),
    },
    ("weekend", "female"): {
        "templates": [
            {"cats": ["티셔츠", "청바지", "스니커즈"], "formality": [2.0, 2.0, 2.0]},
            {"cats": ["맨투맨", "스커트", "스니커즈"], "formality": [2.0, 2.5, 2.0]},
            {"cats": ["원피스", "플랫슈즈"], "formality": [2.5, 2.5]},
        ],
        "moods": ["casual", "relaxed"],
        "style_tag": "casual",
        "formality_range": (1.5, 2.5),
    },
    # workout
    ("workout", "male"): {
        "templates": [
            {"cats": ["조거팬츠", "반팔티", "스니커즈"], "formality": [1.0, 1.0, 1.5]},
            {"cats": ["반바지", "맨투맨", "스니커즈"], "formality": [1.0, 1.5, 1.5]},
            {"cats": ["트레이닝팬츠", "후드", "스니커즈"], "formality": [1.0, 1.0, 1.5]},
        ],
        "moods": ["sporty", "casual"],
        "style_tag": "sporty",
        "formality_range": (1.0, 1.5),
    },
    ("workout", "female"): {
        "templates": [
            {"cats": ["레깅스", "스포츠브라", "스니커즈"], "formality": [1.0, 1.0, 1.5]},
            {"cats": ["조거팬츠", "맨투맨", "스니커즈"], "formality": [1.0, 1.5, 1.5]},
            {"cats": ["레깅스", "반팔티", "바람막이"], "formality": [1.0, 1.0, 1.5]},
        ],
        "moods": ["sporty", "casual"],
        "style_tag": "sporty",
        "formality_range": (1.0, 1.5),
    },
}

# 카테고리별 브랜드 풀
BRAND_POOL = {
    "셔츠": ["유니클로", "자라", "무인양품", "폴로"],
    "슬랙스": ["유니클로", "자라", "COS", "에잇세컨즈"],
    "자켓": ["자라", "COS", "타미힐피거", "폴로"],
    "로퍼": ["탠디", "에스콰이어", "클라크스"],
    "니트": ["유니클로", "자라", "COS", "에잇세컨즈"],
    "스니커즈": ["나이키", "아디다스", "뉴발란스", "컨버스"],
    "후드": ["나이키", "아디다스", "MLB", "챔피온"],
    "맨투맨": ["나이키", "아디다스", "무신사스탠다드", "커버낫"],
    "청바지": ["리바이스", "자라", "유니클로", "무신사스탠다드"],
    "조거팬츠": ["나이키", "아디다스", "푸마", "뉴발란스"],
    "티셔츠": ["유니클로", "무신사스탠다드", "자라", "나이키"],
    "반바지": ["나이키", "아디다스", "유니클로", "자라"],
    "원피스": ["자라", "H&M", "에잇세컨즈", "미쏘"],
    "블라우스": ["자라", "H&M", "에잇세컨즈", "COS"],
    "스커트": ["자라", "H&M", "에잇세컨즈", "COS"],
    "힐": ["소다", "에스콰이어", "나인웨스트"],
    "플랫슈즈": ["소다", "클라크스", "에코"],
    "정장바지": ["자라", "COS", "타미힐피거", "유니클로"],
    "넥타이": ["폴로", "타미힐피거", "브룩스브라더스"],
    "크롭탑": ["자라", "H&M", "에잇세컨즈"],
    "바람막이": ["나이키", "아디다스", "뉴발란스", "K2"],
    "레깅스": ["젝시믹스", "안다르", "나이키", "아디다스"],
    "스포츠브라": ["젝시믹스", "안다르", "나이키", "아디다스"],
    "반팔티": ["나이키", "아디다스", "유니클로", "무신사스탠다드"],
    "트레이닝팬츠": ["나이키", "아디다스", "푸마", "뉴발란스"],
    "모자": ["나이키", "아디다스", "뉴에라", "MLB"],
}

# 카테고리별 가격 범위
PRICE_RANGES = {
    "셔츠": (25000, 60000), "슬랙스": (30000, 70000), "자켓": (60000, 150000),
    "로퍼": (50000, 120000), "니트": (25000, 60000), "스니커즈": (50000, 130000),
    "후드": (30000, 70000), "맨투맨": (25000, 60000), "청바지": (30000, 80000),
    "조거팬츠": (25000, 55000), "티셔츠": (15000, 40000), "반바지": (20000, 45000),
    "원피스": (30000, 80000), "블라우스": (25000, 60000), "스커트": (25000, 60000),
    "힐": (40000, 100000), "플랫슈즈": (30000, 80000), "정장바지": (35000, 80000),
    "넥타이": (15000, 40000), "크롭탑": (15000, 35000), "바람막이": (40000, 90000),
    "레깅스": (25000, 55000), "스포츠브라": (20000, 45000), "반팔티": (15000, 35000),
    "트레이닝팬츠": (25000, 55000), "모자": (15000, 35000),
}


def load_json(name: str) -> list:
    p = DATA_DIR / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def save_json(name: str, data: list) -> None:
    p = DATA_DIR / name
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Saved: {p.name} ({len(data)} items, {p.stat().st_size / 1024:.0f}KB)")


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
    tpo_popularity = {"commute": 0, "date": -2, "interview": -3, "weekend": 1,
                      "campus": -1, "travel": 2, "event": -2, "workout": -5}
    of_adj = sum(tpo_popularity.get(t, 0) for t in tpos)
    of = max(50.0, min(100.0, of_base + of_adj))

    # CH: 색상 조화
    hex_colors = [item.get("color_hex", "") for item in items if item.get("color_hex")]
    if len(hex_colors) >= 2:
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


def generate_outfit(tpo: str, gender: str, tone_id: str, idx: int) -> dict:
    """단일 코디 생성."""
    sig = TPO_SIGNATURES.get((tpo, gender))
    if not sig:
        raise ValueError(f"No signature for ({tpo}, {gender})")

    tmpl = sig["templates"][idx % len(sig["templates"])]
    cats = tmpl["cats"]
    formalities = tmpl["formality"]

    colors = TONE_REPRESENTATIVE_COLORS.get(tone_id, ["#808080"])
    outfit_id = f"fill_{tpo}_{gender}_{tone_id}_{idx:03d}"

    items = []
    for i, cat in enumerate(cats):
        brand_pool = BRAND_POOL.get(cat, ["브랜드"])
        price_min, price_max = PRICE_RANGES.get(cat, (20000, 60000))
        item = {
            "product_id": hashlib.md5(f"{outfit_id}_{cat}_{i}".encode()).hexdigest()[:12],
            "name": f"{cat} ({tone_id.replace('_', ' ')})",
            "category": cat,
            "price": random.randint(price_min, price_max),
            "image_url": "",
            "formality": formalities[i],
            "silhouette": "regular",
            "tone_id": tone_id,
            "color_hex": random.choice(colors),
            "brand": random.choice(brand_pool),
            "gender": gender,
            "mall_name": random.choice(brand_pool),
            "mall_url": "",
            "style_tag": sig["style_tag"],
        }
        items.append(item)

    total_price = sum(it["price"] for it in items)
    f_avg = round(sum(formalities) / len(formalities), 1)

    outfit = {
        "outfit_id": outfit_id,
        "tone_id": tone_id,
        "gender": gender,
        "designed_tpo": [tpo],
        "designed_moods": sig["moods"],
        "items": items,
        "formality_avg": f_avg,
        "price_total": total_price,
        "total_price": total_price,
        "llm_quality_score": 3,
        "eval_detail": {
            "style_cohesion": 3,
            "silhouette_balance": 3,
            "trend_relevance": 3,
            "material_harmony": 3,
            "overall_styling": 3,
            "comment": "auto-generated to fill data gap",
        },
        "tags": [tpo, sig["style_tag"]] + sig["moods"],
        "is_complete_outfit": True,
        "style_tag": sig["style_tag"],
    }
    outfit["scores"] = compute_scores(outfit)
    return outfit


def count_combos(outfits: list[dict]) -> dict[tuple, int]:
    """(tpo, gender, tone) → count 맵."""
    counts = defaultdict(int)
    for o in outfits:
        if not o.get("scores") or not o["scores"].get("total"):
            continue
        gender = o.get("gender", "")
        tone = o.get("tone_id", "")
        for tpo in (o.get("designed_tpo") or []):
            tpo = tpo.lower()
            counts[(tpo, gender, tone)] += 1
    return counts


def main():
    print("=" * 60)
    print("ColorFit 데이터 갭 보충")
    print("=" * 60)

    # 백업
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    src = DATA_DIR / "outfits_scored.json"
    dst = DATA_DIR / f"outfits_scored_backup_{ts}.json"
    shutil.copy2(src, dst)
    print(f"\n[0] 백업 완료: {dst.name}")

    outfits = load_json("outfits_scored.json")
    total_before = len(outfits)
    print(f"[1] 원본 로드: {total_before}개 코디")

    # 현재 분포 분석
    counts = count_combos(outfits)

    zero_before = 0
    under5_before = 0
    for tpo in TPOS:
        for gender in ["female", "male"]:
            for tone in TONE_IDS:
                c = counts[(tpo, gender, tone)]
                if c == 0:
                    zero_before += 1
                if c < MIN_COUNT:
                    under5_before += 1

    print(f"\n[2] 현재 분포:")
    print(f"  0개 조합: {zero_before}")
    print(f"  <5 조합: {under5_before}")

    # 부족 조합 식별 + 코디 생성
    new_outfits = []
    fill_log = defaultdict(int)

    for tpo in TPOS:
        for gender in ["female", "male"]:
            for tone in TONE_IDS:
                current = counts[(tpo, gender, tone)]
                if current >= MIN_COUNT:
                    continue

                needed = MIN_COUNT - current
                sig_key = (tpo, gender)
                if sig_key not in TPO_SIGNATURES:
                    print(f"  [WARN] No signature for {sig_key}, skipping")
                    continue

                for i in range(needed):
                    # Use unique index: current count + i to avoid template duplication
                    outfit = generate_outfit(tpo, gender, tone, current + i)
                    new_outfits.append(outfit)
                    fill_log[(tpo, gender)] += 1

    outfits.extend(new_outfits)
    total_after = len(outfits)

    print(f"\n[3] 생성 완료: {len(new_outfits)}개 코디 추가")
    print(f"\n  TPO별 생성 수:")
    for (tpo, gender), cnt in sorted(fill_log.items()):
        print(f"    {tpo:<12} {gender:<8} +{cnt}")

    # 저장
    save_json("outfits_scored.json", outfits)

    # 검증
    counts_after = count_combos(outfits)
    zero_after = 0
    under5_after = 0
    for tpo in TPOS:
        for gender in ["female", "male"]:
            for tone in TONE_IDS:
                c = counts_after[(tpo, gender, tone)]
                if c == 0:
                    zero_after += 1
                if c < MIN_COUNT:
                    under5_after += 1

    print(f"\n{'=' * 60}")
    print(f"검증 결과")
    print(f"{'=' * 60}")
    print(f"총 코디: {total_before} → {total_after} (+{total_after - total_before})")
    print(f"0개 조합: {zero_before} → {zero_after}")
    print(f"<5 조합: {under5_before} → {under5_after}")

    print(f"\nTPO×성별 분포 (스코어 있는 코디):")
    for tpo in TPOS:
        for gender in ["female", "male"]:
            total = sum(counts_after[(tpo, gender, t)] for t in TONE_IDS)
            zeros = sum(1 for t in TONE_IDS if counts_after[(tpo, gender, t)] == 0)
            min_c = min(counts_after[(tpo, gender, t)] for t in TONE_IDS)
            max_c = max(counts_after[(tpo, gender, t)] for t in TONE_IDS)
            print(f"  {tpo:<12} {gender:<8} total={total:>4}  min={min_c}  max={max_c}  zeros={zeros}")

    # 스코어 분포
    totals = [o["scores"]["total"] for o in outfits if o.get("scores") and o["scores"].get("total")]
    if totals:
        totals.sort()
        print(f"\n스코어 분포:")
        print(f"  min={totals[0]:.1f}, median={totals[len(totals)//2]:.1f}, max={totals[-1]:.1f}")
        print(f"  70+: {sum(1 for t in totals if t >= 70)}, 80+: {sum(1 for t in totals if t >= 80)}")


if __name__ == "__main__":
    random.seed(42)
    main()
