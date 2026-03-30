"""
run_pipeline.py — 정규화된 상품에 분류 + 톤매핑을 일괄 적용하고 코디를 생성한다.

사용법:
    python -m backend.scripts.run_pipeline
    python -m backend.scripts.run_pipeline --skip-classify  # 분류 건너뛰기
"""

import argparse
import json
import logging
import time
from pathlib import Path

from backend.scripts.classifier import classify_product
from backend.scripts.generate_outfits import generate_all, ALL_TONES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "backend" / "data"
NORMALIZED_DIR = DATA_DIR / "normalized"


def classify_all_products():
    """정규화된 전체 상품에 카테고리 분류를 적용한다."""
    stats = {"total": 0, "keyword": 0, "cache": 0, "gemini": 0, "fallback": 0}

    for tone_id in ALL_TONES:
        path = NORMALIZED_DIR / f"{tone_id}.json"
        if not path.exists():
            continue

        with open(path, "r", encoding="utf-8") as f:
            products = json.load(f)

        for p in products:
            # source_tone을 tone_id로 사용 (이미지 색상 추출 대체)
            p["tone_id"] = p.get("source_tone", tone_id)

            # 카테고리 분류
            cat_hint = " ".join(filter(None, [
                p.get("category1", ""),
                p.get("category2", ""),
                p.get("category3", ""),
                p.get("category4", ""),
            ]))

            result = classify_product(
                p.get("product_id", ""),
                p.get("name", ""),
                cat_hint=cat_hint,
                use_llm=False,  # 배치에서는 키워드만 사용 (속도)
            )

            p["category"] = result["category"]
            p["silhouette"] = result["silhouette"]
            p["formality"] = result["formality"]
            p["gender"] = result["gender"]
            p["tpo"] = result["tpo"]

            stats["total"] += 1
            stats[result.get("_method", "fallback")] += 1

        # 저장
        with open(path, "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)

        classified = stats["total"]
        keyword_rate = stats["keyword"] / max(classified, 1) * 100
        logger.info(
            "[%s] %d개 분류 완료 (keyword: %.0f%%)",
            tone_id, len(products), keyword_rate,
        )

    logger.info(
        "전체 분류 완료: %d개 (keyword: %d, fallback: %d)",
        stats["total"], stats["keyword"], stats["fallback"],
    )
    return stats


def print_category_stats():
    """카테고리 분포를 출력한다."""
    cat_counts: dict[str, int] = {}
    gender_counts: dict[str, int] = {}
    total = 0

    for tone_id in ALL_TONES:
        path = NORMALIZED_DIR / f"{tone_id}.json"
        if not path.exists():
            continue
        with open(path, "r", encoding="utf-8") as f:
            products = json.load(f)
        for p in products:
            cat = p.get("category", "unknown")
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
            gender = p.get("gender", "unisex")
            gender_counts[gender] = gender_counts.get(gender, 0) + 1
            total += 1

    logger.info("=== 카테고리 분포 (상위 15) ===")
    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1])[:15]:
        logger.info("  %-15s %6d (%4.1f%%)", cat, count, count / total * 100)

    logger.info("=== 성별 분포 ===")
    for g, count in sorted(gender_counts.items(), key=lambda x: -x[1]):
        logger.info("  %-10s %6d (%4.1f%%)", g, count, count / total * 100)


def main():
    parser = argparse.ArgumentParser(description="전처리 파이프라인 실행")
    parser.add_argument("--skip-classify", action="store_true")
    parser.add_argument("--skip-outfits", action="store_true")
    args = parser.parse_args()

    # Step 1: 분류
    if not args.skip_classify:
        logger.info("=" * 50)
        logger.info("Step 1: 카테고리 분류 시작")
        logger.info("=" * 50)
        t0 = time.time()
        classify_all_products()
        logger.info("분류 소요 시간: %.1f초", time.time() - t0)
        print_category_stats()

    # Step 2: 코디 생성
    if not args.skip_outfits:
        logger.info("=" * 50)
        logger.info("Step 2: 코디 조합 생성 시작")
        logger.info("=" * 50)
        t0 = time.time()
        outfits = generate_all()
        logger.info("코디 생성 소요 시간: %.1f초", time.time() - t0)
        logger.info("생성된 코디: %d개", len(outfits))

    logger.info("파이프라인 완료!")


if __name__ == "__main__":
    main()
