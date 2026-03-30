"""
rebuild_from_tones.py — raw 수집 데이터를 정규화하여 NormalizedProduct로 변환

사용법:
    python -m backend.scripts.rebuild_from_tones
    python -m backend.scripts.rebuild_from_tones --tone spring_warm_light
"""

import argparse
import json
import logging
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "backend" / "data"
RAW_DIR = DATA_DIR / "raw"
OUTPUT_DIR = DATA_DIR / "normalized"

BRAND_WHITELIST_PATH = DATA_DIR / "brand_whitelist.json"

ALL_TONES = [
    "spring_warm_light", "spring_warm_bright", "spring_warm_mute",
    "summer_cool_light", "summer_cool_soft", "summer_cool_mute",
    "autumn_warm_deep", "autumn_warm_mute", "autumn_warm_bright",
    "winter_cool_deep", "winter_cool_bright", "winter_cool_light",
]


@dataclass
class NormalizedProduct:
    product_id: str
    name: str
    brand: str
    category: str  # Task 1.8에서 분류
    color_hex: list[str] = field(default_factory=list)  # Task 1.7에서 추출
    tone_id: str = ""  # Task 1.7에서 매핑
    price: int = 0
    mall_name: str = ""
    mall_url: str = ""
    image_url: str = ""
    tags: list[str] = field(default_factory=list)
    source_tone: str = ""  # 수집 시 타겟 톤
    category1: str = ""
    category2: str = ""
    category3: str = ""
    category4: str = ""
    gender: str = ""  # Task 1.8에서 분류
    silhouette: str = ""  # Task 1.8에서 분류
    formality: int = 0  # Task 1.8에서 분류
    tpo: list[str] = field(default_factory=list)  # Task 1.8에서 분류


# ── HTML 태그 제거 ──────────────────────────────────────────

HTML_TAG_RE = re.compile(r"<[^>]+>")


def strip_html(text: str) -> str:
    """HTML 태그를 제거하고 연속 공백을 정리한다."""
    cleaned = HTML_TAG_RE.sub("", text)
    return " ".join(cleaned.split())


# ── 브랜드 추출 ─────────────────────────────────────────────

_brand_whitelist: list[str] | None = None


def _load_brand_whitelist() -> list[str]:
    global _brand_whitelist
    if _brand_whitelist is None:
        with open(BRAND_WHITELIST_PATH, "r", encoding="utf-8") as f:
            _brand_whitelist = json.load(f)
        # 긴 이름부터 매칭 (예: "무신사 스탠다드 우먼" > "무신사 스탠다드")
        _brand_whitelist.sort(key=len, reverse=True)
    return _brand_whitelist


def extract_brand(title: str, mall_name: str, raw_brand: str = "") -> str:
    """브랜드명을 추출한다. raw API brand → title 매칭 → mallName 순으로 시도."""
    whitelist = _load_brand_whitelist()

    # 1) API의 brand 필드가 화이트리스트에 있으면 사용
    if raw_brand:
        for wb in whitelist:
            if wb.lower() == raw_brand.lower():
                return wb

    # 2) 상품명에서 화이트리스트 브랜드 매칭
    title_lower = title.lower()
    for wb in whitelist:
        if wb.lower() in title_lower:
            return wb

    # 3) mallName이 화이트리스트에 있으면 사용
    if mall_name:
        for wb in whitelist:
            if wb.lower() == mall_name.lower():
                return wb

    # 4) mallName 그대로 사용 (화이트리스트 외)
    return mall_name or ""


# ── 가격 파싱 ───────────────────────────────────────────────

def parse_price(lprice: str, hprice: str = "") -> int:
    """가격 문자열을 int로 변환한다. lprice 우선."""
    for p in [lprice, hprice]:
        if p and p.isdigit():
            return int(p)
    return 0


# ── 정규화 메인 ─────────────────────────────────────────────

def normalize_item(raw: dict, source_tone: str) -> NormalizedProduct:
    """raw API 응답 아이템을 NormalizedProduct로 변환한다."""
    title = strip_html(raw.get("title", ""))
    brand = extract_brand(
        title,
        raw.get("mallName", ""),
        raw.get("brand", ""),
    )

    return NormalizedProduct(
        product_id=str(raw.get("productId", "")),
        name=title,
        brand=brand,
        category="",  # Task 1.8에서 채움
        price=parse_price(raw.get("lprice", ""), raw.get("hprice", "")),
        mall_name=raw.get("mallName", ""),
        mall_url=raw.get("link", ""),
        image_url=raw.get("image", ""),
        source_tone=source_tone,
        category1=raw.get("category1", ""),
        category2=raw.get("category2", ""),
        category3=raw.get("category3", ""),
        category4=raw.get("category4", ""),
    )


def normalize_tone(tone_id: str) -> list[dict]:
    """특정 톤의 raw JSON을 정규화한다."""
    raw_path = RAW_DIR / f"{tone_id}.json"
    if not raw_path.exists():
        logger.warning("[%s] raw 파일 없음: %s", tone_id, raw_path)
        return []

    with open(raw_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    items = raw_data.get("items", [])
    normalized = [asdict(normalize_item(item, tone_id)) for item in items]

    logger.info("[%s] %d개 정규화 완료", tone_id, len(normalized))
    return normalized


def run(tones: list[str]):
    """지정된 톤들의 raw 데이터를 정규화하여 저장한다."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_products = []
    for tone_id in tones:
        products = normalize_tone(tone_id)
        all_products.extend(products)

    if not all_products:
        logger.warning("정규화할 데이터가 없습니다. Task 1.5를 먼저 실행하세요.")
        return

    # 톤별 개별 저장
    by_tone: dict[str, list[dict]] = {}
    for p in all_products:
        t = p["source_tone"]
        by_tone.setdefault(t, []).append(p)

    for tone_id, products in by_tone.items():
        out_path = OUTPUT_DIR / f"{tone_id}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        logger.info("[%s] → %s (%d개)", tone_id, out_path, len(products))

    # 전체 통합 파일
    merged_path = OUTPUT_DIR / "all_products.json"
    with open(merged_path, "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)

    logger.info("전체 %d개 정규화 완료 → %s", len(all_products), merged_path)


def main():
    parser = argparse.ArgumentParser(description="raw 상품 데이터 정규화")
    parser.add_argument("--tone", type=str, choices=ALL_TONES, help="특정 톤만 처리")
    args = parser.parse_args()

    tones = [args.tone] if args.tone else ALL_TONES
    run(tones)


if __name__ == "__main__":
    main()
