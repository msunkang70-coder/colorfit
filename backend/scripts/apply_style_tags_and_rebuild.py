"""
스타일링 엔진 v3 — 스타일 태그 기반 코디 생성.

1. 아이템에 style_tag 자동 부여 (minimal/casual/feminine/formal/sporty)
2. TPO × 스타일 조합으로 코디 생성
3. Top3 다양성: 서로 다른 style_tag 강제
4. 연령 필터 강화

사용법:
    cd backend
    python -m scripts.apply_style_tags_and_rebuild
"""

import json
import hashlib
import random
from collections import Counter, defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SCORED_PATH = DATA_DIR / "outfits_scored.json"
TEMPLATE_PATH = DATA_DIR / "styling_templates.json"

random.seed(42)

# ── 스타일 태그 규칙 ──

STYLE_RULES = {
    # 카테고리 기반 기본 스타일
    "formal": {"자켓", "블라우스", "힐", "로퍼"},
    "casual": {"후드", "맨투맨", "청바지", "스니커즈", "반팔"},
    "feminine": {"스커트", "원피스", "크로스백", "가디건"},
    "sporty": {"크롭탑", "탱크탑", "레깅스", "숏팬츠", "조거팬츠"},
    "minimal": {"셔츠", "슬랙스", "니트", "와이드팬츠", "코트"},
}

# 브랜드 기반 스타일 보정
BRAND_STYLE = {
    "cos": "minimal", "코스": "minimal",
    "자라": "minimal", "zara": "minimal",
    "h&m": "casual", "에이치앤엠": "casual",
    "빈폴": "formal", "헤지스": "formal",
    "타미힐피거": "formal", "폴로": "formal",
    "에잇세컨즈": "casual",
    "나이키": "sporty", "아디다스": "sporty",
    "안다르": "sporty", "젝시믹스": "sporty",
}

# 상품명 키워드 기반 스타일 보정
NAME_STYLE_KEYWORDS = {
    "formal": ["정장", "포멀", "면접", "비즈니스", "오피스"],
    "casual": ["캐주얼", "데일리", "편한", "루즈", "오버핏"],
    "feminine": ["리본", "프릴", "레이스", "플리츠", "플로럴", "꽃무늬"],
    "sporty": ["운동", "트레이닝", "애슬레저", "짐"],
    "minimal": ["미니멀", "베이직", "심플", "클린"],
}

# TPO별 선호 스타일 (이 스타일의 코디를 우선 생성)
TPO_PREFERRED_STYLES = {
    "interview": ["formal", "minimal"],
    "commute": ["minimal", "formal"],
    "date": ["feminine", "minimal", "casual"],
    "campus": ["casual", "sporty"],
    "weekend": ["casual", "minimal"],
    "travel": ["casual", "sporty"],
    "event": ["formal", "feminine"],
    "workout": ["sporty"],
}

# 품질 점수 (이전과 동일)
LOW_QUALITY_BRANDS = ["temu", "쿠팡", "11번가", "위메프", "알리익스프레스"]
LOW_QUALITY_KEYWORDS = ["자전거", "방한화", "작업복", "안전화", "매트리스", "침대", "커튼",
                        "이불", "수면", "잠옷", "강아지", "반려", "엄마", "할머니", "중년"]
HIGH_QUALITY_BRANDS = ["코스", "cos", "빈폴", "헤지스", "타미힐피거", "폴로", "마시모두띠",
                       "잇미샤", "리스트", "에잇세컨즈", "무신사 스탠다드", "지오다노",
                       "캘빈클라인", "h&m", "자라", "zara"]


def classify_style(item: dict) -> str:
    """아이템의 스타일 태그 결정."""
    cat = item.get("category", "")
    name = item.get("name", "").lower()
    brand = item.get("brand", "").lower()
    mall = item.get("mall_name", "").lower()
    combined = f"{name} {brand} {mall}"

    # 1. 브랜드 기반 (가장 강력)
    for keyword, style in BRAND_STYLE.items():
        if keyword in combined:
            return style

    # 2. 상품명 키워드
    for style, keywords in NAME_STYLE_KEYWORDS.items():
        for kw in keywords:
            if kw in name:
                return style

    # 3. 카테고리 기반 (fallback)
    for style, cats in STYLE_RULES.items():
        if cat in cats:
            return style

    return "casual"  # 기본값


def item_quality_score(item: dict) -> float:
    score = 50.0
    name = item.get("name", "").lower()
    brand = item.get("brand", "").lower()
    combined = f"{name} {brand} {item.get('mall_name', '').lower()}"
    price = item.get("price", 0)

    for lb in LOW_QUALITY_BRANDS:
        if lb in combined:
            score -= 30; break
    for kw in LOW_QUALITY_KEYWORDS:
        if kw in name:
            score -= 40; break
    for hb in HIGH_QUALITY_BRANDS:
        if hb in combined:
            score += 25; break
    if price < 10000: score -= 15
    elif 30000 <= price <= 200000: score += 10
    if not item.get("image_url"): score -= 50
    return max(0, min(100, score))


def pick_best_by_style(items: list[dict], style: str, used_pids: set) -> dict | None:
    """지정 스타일에 맞는 고품질 아이템 선택."""
    candidates = []
    for it in items:
        if it.get("product_id") in used_pids:
            continue
        q = item_quality_score(it)
        if q < 30:
            continue
        s = classify_style(it)
        # 스타일 매칭 보너스
        style_bonus = 20 if s == style else 0
        candidates.append((it, q + style_bonus))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[1], reverse=True)
    top = candidates[:min(5, len(candidates))]
    return random.choice(top)[0]


def main():
    with open(SCORED_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        templates = json.load(f)

    # 1. 모든 아이템에 style_tag 부여
    style_counter = Counter()
    for o in data:
        for it in o.get("items", []):
            tag = classify_style(it)
            it["style_tag"] = tag
            style_counter[tag] += 1

    print("=== 스타일 태그 분포 ===")
    for s, c in style_counter.most_common():
        print(f"  {s}: {c}")

    # 2. 기존 styled_ 제거
    base = [o for o in data if not o.get("outfit_id", "").startswith("styled_")]
    print(f"\n베이스 코디: {len(base)}건")

    # 3. 아이템 풀 (카테고리 × 성별 × 스타일)
    pool = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    seen = set()
    for o in base:
        oid = o.get("outfit_id", "")
        gender = "female" if "female" in oid else "male"
        for it in o.get("items", []):
            pid = it.get("product_id", "")
            cat = it.get("category", "")
            style = it.get("style_tag", "casual")
            if not pid or not cat or pid in seen or item_quality_score(it) < 30:
                continue
            seen.add(pid)
            pool[cat][gender][style].append(it)
            pool[cat][gender]["all"].append(it)  # fallback용

    # 4. 스타일 기반 코디 생성
    new_outfits = []
    existing_ids = {o.get("outfit_id") for o in base}

    for tpo, genders in templates.items():
        preferred_styles = TPO_PREFERRED_STYLES.get(tpo, ["casual", "minimal"])

        for gender, tmpls in genders.items():
            for tmpl in tmpls:
                slots = tmpl["slots"]
                name = tmpl["name"]

                # 각 선호 스타일로 코디 생성 시도
                for style in preferred_styles:
                    for idx in range(5):
                        items = []
                        used_pids = set()
                        success = True

                        for cat in slots:
                            # 해당 스타일 아이템 우선, 없으면 all에서
                            cat_items = pool.get(cat, {}).get(gender, {}).get(style, [])
                            if len(cat_items) < 2:
                                cat_items = pool.get(cat, {}).get(gender, {}).get("all", [])
                            if not cat_items:
                                for g in pool.get(cat, {}):
                                    cat_items = pool[cat][g].get("all", [])
                                    if cat_items:
                                        break

                            if not cat_items:
                                success = False
                                break

                            it = pick_best_by_style(cat_items, style, used_pids)
                            if not it:
                                success = False
                                break
                            items.append(it)
                            used_pids.add(it.get("product_id"))

                        if not success:
                            continue

                        outfit_quality = sum(item_quality_score(it) for it in items) / len(items)
                        if outfit_quality < 50:
                            continue

                        h = hashlib.md5(f"{tpo}_{gender}_{name}_{style}_{idx}_v3".encode()).hexdigest()[:8]
                        oid = f"styled_{tpo}_{gender}_{h}"
                        if oid in existing_ids:
                            continue

                        total_price = sum(it.get("price", 0) for it in items)
                        outfit = {
                            "outfit_id": oid,
                            "items": items,
                            "designed_tpo": [tpo],
                            "tags": [tpo, style, "spring", "autumn"],
                            "total_price": total_price,
                            "is_complete_outfit": True,
                            "template": name,
                            "style_tag": style,
                            "quality_score": round(outfit_quality, 1),
                        }
                        new_outfits.append(outfit)
                        existing_ids.add(oid)

    # 기존 코디에도 style_tag 부여
    for o in base:
        if not o.get("style_tag"):
            styles = [it.get("style_tag", "casual") for it in o.get("items", [])]
            o["style_tag"] = max(set(styles), key=styles.count) if styles else "casual"

    combined = base + new_outfits
    with open(SCORED_PATH, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False)

    # 통계
    tpo_counter = Counter()
    style_outfit_counter = Counter()
    for o in combined:
        for t in o.get("designed_tpo", []):
            tpo_counter[t] += 1
        style_outfit_counter[o.get("style_tag", "?")] += 1

    print(f"\n새 코디: {len(new_outfits)}건")
    print(f"최종: {len(combined)}건")
    print(f"\nTPO:")
    for t, c in tpo_counter.most_common():
        print(f"  {t}: {c}")
    print(f"\n스타일 분포:")
    for s, c in style_outfit_counter.most_common():
        print(f"  {s}: {c}")

    # Top3 다양성 검증
    print(f"\n=== Top3 다양성 샘플 ===")
    for tpo in ["interview", "commute", "date"]:
        outfits = [o for o in combined if tpo in o.get("designed_tpo", [])]
        styles_seen = set()
        top3 = []
        for o in sorted(outfits, key=lambda x: x.get("quality_score", 0), reverse=True):
            s = o.get("style_tag", "?")
            if s not in styles_seen:
                top3.append(o)
                styles_seen.add(s)
            if len(top3) >= 3:
                break
        print(f"\n  {tpo}:")
        for i, o in enumerate(top3):
            cats = [it.get("category") for it in o.get("items", [])]
            print(f"    Top{i+1}: [{o.get('style_tag')}] {cats} ₩{o.get('total_price',0):,} q={o.get('quality_score',0)}")


if __name__ == "__main__":
    main()
