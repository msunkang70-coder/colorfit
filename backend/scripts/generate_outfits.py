"""
generate_outfits.py — 레시피 기반 코디 조합 생성

사용법:
    python -m backend.scripts.generate_outfits
    python -m backend.scripts.generate_outfits --tone spring_warm_light
    python -m backend.scripts.generate_outfits --gender female
"""

import argparse
import hashlib
import json
import logging
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "backend" / "data"
NORMALIZED_DIR = DATA_DIR / "normalized"
RECIPES_PATH = DATA_DIR / "outfit_recipes.json"
OUTPUT_PATH = DATA_DIR / "outfits.json"

ALL_TONES = [
    "spring_warm_light", "spring_warm_bright", "spring_warm_mute",
    "summer_cool_light", "summer_cool_soft", "summer_cool_mute",
    "autumn_warm_deep", "autumn_warm_mute", "autumn_warm_bright",
    "winter_cool_deep", "winter_cool_bright", "winter_cool_light",
]


@dataclass
class Outfit:
    outfit_id: str
    tone_id: str
    gender: str
    designed_tpo: str
    designed_moods: list[str]
    items: list[dict]  # [{product_id, name, category, price, image_url, ...}]
    formality_avg: float = 0.0
    price_total: int = 0
    llm_quality_score: int | None = None


# ── 상품 풀 로딩 ────────────────────────────────────────────

def load_product_pool(tone_id: str) -> list[dict]:
    """정규화된 상품 풀을 로드한다."""
    path = NORMALIZED_DIR / f"{tone_id}.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_recipes() -> dict:
    """레시피 JSON을 로드한다."""
    with open(RECIPES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ── 검증 함수들 ─────────────────────────────────────────────

def check_forbidden(items: list[dict], forbidden: list[str]) -> bool:
    """금지 카테고리가 포함되어 있지 않은지 검증."""
    for item in items:
        if item.get("category") in forbidden:
            return False
    return True


def check_formality(items: list[dict], formality_range: list[int]) -> bool:
    """포멀도 편차 ≤ 2, 범위 내 확인."""
    formalities = [item.get("formality", 3) for item in items]
    if not formalities:
        return True

    avg = sum(formalities) / len(formalities)
    if avg < formality_range[0] or avg > formality_range[1]:
        return False

    if max(formalities) - min(formalities) > 2:
        return False

    return True


def check_price_ratio(items: list[dict], max_ratio: float = 5.0) -> bool:
    """가격 비율이 max_ratio 이내인지 확인."""
    prices = [item.get("price", 0) for item in items if item.get("price", 0) > 0]
    if len(prices) < 2:
        return True
    return max(prices) / min(prices) <= max_ratio


def outfit_hash(items: list[dict]) -> str:
    """아이템 조합의 고유 해시 (중복 방지)."""
    ids = sorted(item.get("product_id", "") for item in items)
    return hashlib.md5("|".join(ids).encode()).hexdigest()


# ── 아이템 선택 ─────────────────────────────────────────────

def pick_items_for_slot(
    pool: list[dict],
    category_options: list[str],
    used_ids: set[str],
) -> dict | None:
    """카테고리 옵션 중 하나에 해당하는 아이템을 랜덤 선택."""
    candidates = [
        p for p in pool
        if p.get("category") in category_options
        and p.get("product_id") not in used_ids
    ]
    if not candidates:
        return None
    return random.choice(candidates)


def pick_optional_item(
    pool: list[dict],
    category: str,
    used_ids: set[str],
    probability: float = 0.6,
) -> dict | None:
    """선택 카테고리 아이템을 확률적으로 추가."""
    if random.random() > probability:
        return None

    candidates = [
        p for p in pool
        if p.get("category") == category
        and p.get("product_id") not in used_ids
    ]
    if not candidates:
        return None
    return random.choice(candidates)


# ── 코디 생성 메인 ──────────────────────────────────────────

def generate_for_recipe(
    pool: list[dict],
    recipe: dict,
    tone_id: str,
    gender: str,
    existing_hashes: set[str],
) -> list[Outfit]:
    """단일 레시피에 대해 코디를 생성한다."""
    target = recipe.get("target_count", 10)
    generated = []
    max_attempts = target * 20  # 무한 루프 방지
    attempts = 0

    # 성별 필터링
    gender_pool = [
        p for p in pool
        if p.get("gender", "unisex") in (gender, "unisex")
    ]

    while len(generated) < target and attempts < max_attempts:
        attempts += 1
        items = []
        used_ids: set[str] = set()

        # 1. 필수 카테고리 선택
        required_ok = True
        for slot in recipe["required"]:
            item = pick_items_for_slot(gender_pool, slot, used_ids)
            if item is None:
                required_ok = False
                break
            items.append(item)
            used_ids.add(item.get("product_id", ""))

        if not required_ok:
            continue

        # 2. 선택 카테고리 확률적 추가
        optional_probs = {"스니커즈": 0.6, "로퍼": 0.6, "힐": 0.5, "부츠": 0.5,
                          "자켓": 0.25, "코트": 0.2, "가디건": 0.3, "점퍼": 0.25,
                          "토트백": 0.3, "크로스백": 0.3, "샌들": 0.4}
        for opt_cat in recipe.get("optional", []):
            prob = optional_probs.get(opt_cat, 0.4)
            opt_item = pick_optional_item(gender_pool, opt_cat, used_ids, prob)
            if opt_item:
                items.append(opt_item)
                used_ids.add(opt_item.get("product_id", ""))

        # 3. 금지 카테고리 검증
        if not check_forbidden(items, recipe.get("forbidden", [])):
            continue

        # 4. 포멀도 검증
        if not check_formality(items, recipe.get("formality_range", [1, 5])):
            continue

        # 5. 가격 비율 검증
        if not check_price_ratio(items):
            continue

        # 6. 중복 검증
        h = outfit_hash(items)
        if h in existing_hashes:
            continue
        existing_hashes.add(h)

        # 코디 생성 성공
        formalities = [i.get("formality", 3) for i in items]
        prices = [i.get("price", 0) for i in items]

        outfit = Outfit(
            outfit_id=f"{tone_id}_{gender}_{recipe['tpo']}_{len(generated)+1:03d}",
            tone_id=tone_id,
            gender=gender,
            designed_tpo=recipe["tpo"],
            designed_moods=recipe.get("moods", []),
            items=[{
                "product_id": i.get("product_id"),
                "name": i.get("name"),
                "category": i.get("category"),
                "price": i.get("price"),
                "image_url": i.get("image_url"),
                "formality": i.get("formality"),
                "silhouette": i.get("silhouette"),
            } for i in items],
            formality_avg=round(sum(formalities) / len(formalities), 1) if formalities else 0,
            price_total=sum(prices),
        )
        generated.append(outfit)

    if len(generated) < target:
        logger.warning(
            "[%s/%s/%s] 목표 %d개 중 %d개만 생성 (상품 풀 부족)",
            tone_id, gender, recipe["tpo"], target, len(generated),
        )

    return generated


def generate_all(tones: list[str] | None = None, genders: list[str] | None = None):
    """전체 코디를 생성한다."""
    recipes = load_recipes()
    tones = tones or ALL_TONES
    genders = genders or ["female", "male"]

    all_outfits = []
    existing_hashes: set[str] = set()

    for tone_id in tones:
        pool = load_product_pool(tone_id)
        if not pool:
            logger.warning("[%s] 상품 풀 없음. 건너뜀.", tone_id)
            continue

        for gender in genders:
            gender_recipes = recipes.get(gender, [])
            for recipe in gender_recipes:
                outfits = generate_for_recipe(
                    pool, recipe, tone_id, gender, existing_hashes
                )
                all_outfits.extend(outfits)
                if outfits:
                    logger.info(
                        "[%s/%s/%s] %d개 생성",
                        tone_id, gender, recipe["tpo"], len(outfits),
                    )

    # 저장
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(
            [asdict(o) for o in all_outfits],
            f,
            ensure_ascii=False,
            indent=2,
        )

    logger.info("전체 %d개 코디 생성 → %s", len(all_outfits), OUTPUT_PATH)
    return all_outfits


def main():
    parser = argparse.ArgumentParser(description="레시피 기반 코디 조합 생성")
    parser.add_argument("--tone", type=str, choices=ALL_TONES)
    parser.add_argument("--gender", type=str, choices=["female", "male"])
    args = parser.parse_args()

    tones = [args.tone] if args.tone else None
    genders = [args.gender] if args.gender else None
    generate_all(tones=tones, genders=genders)


if __name__ == "__main__":
    main()
