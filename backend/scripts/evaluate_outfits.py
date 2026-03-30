"""
evaluate_outfits.py — Gemini Flash 배치 코디 품질 평가

사용법:
    python -m backend.scripts.evaluate_outfits
    python -m backend.scripts.evaluate_outfits --min-score 3 --dry-run
"""

import argparse
import asyncio
import json
import logging
import os
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "backend" / "data"
OUTFITS_PATH = DATA_DIR / "outfits.json"
EVALUATED_PATH = DATA_DIR / "outfits_evaluated.json"
CACHE_PATH = DATA_DIR / "eval_cache.json"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MAX_CONCURRENT = 5

EVAL_PROMPT = """패션 코디네이션을 평가해주세요.

코디 구성:
{items_text}

TPO: {tpo}
무드: {moods}

아래 5개 축으로 1~5점 평가하고, JSON으로만 응답해주세요:
{{
  "style_cohesion": (1~5, 스타일 통일감),
  "silhouette_balance": (1~5, 실루엣 밸런스),
  "trend_relevance": (1~5, 트렌드 적합도),
  "material_harmony": (1~5, 소재 조화),
  "overall_styling": (1~5, 전체 스타일링 완성도),
  "comment": "(한 줄 평가 코멘트)"
}}"""

WEIGHTS = {
    "style_cohesion": 0.30,
    "silhouette_balance": 0.25,
    "trend_relevance": 0.15,
    "material_harmony": 0.15,
    "overall_styling": 0.15,
}


# ── 캐시 ────────────────────────────────────────────────────

def load_cache() -> dict:
    if CACHE_PATH.exists():
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache: dict):
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


# ── Gemini 평가 ─────────────────────────────────────────────

def format_items(items: list[dict]) -> str:
    """코디 아이템들을 텍스트로 포맷한다."""
    lines = []
    for i, item in enumerate(items, 1):
        cat = item.get("category", "unknown")
        name = item.get("name", "")
        price = item.get("price", 0)
        lines.append(f"{i}. [{cat}] {name} (₩{price:,})")
    return "\n".join(lines)


def calculate_weighted_score(scores: dict) -> float:
    """가중 평균 점수를 계산한다."""
    total = 0.0
    for axis, weight in WEIGHTS.items():
        total += scores.get(axis, 3) * weight
    return round(total, 2)


def evaluate_single(outfit: dict) -> dict | None:
    """단일 코디를 Gemini로 평가한다."""
    if not GEMINI_API_KEY:
        return None

    try:
        import google.generativeai as genai

        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")

        prompt = EVAL_PROMPT.format(
            items_text=format_items(outfit.get("items", [])),
            tpo=outfit.get("designed_tpo", ""),
            moods=", ".join(outfit.get("designed_moods", [])),
        )

        response = model.generate_content(prompt)
        text = response.text.strip()

        # JSON 추출
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        return json.loads(text)
    except Exception as e:
        logger.error("평가 실패 [%s]: %s", outfit.get("outfit_id"), e)
        return None


def evaluate_batch(
    outfits: list[dict],
    min_score: int = 3,
    dry_run: bool = False,
) -> tuple[list[dict], dict]:
    """
    코디 배치를 평가하고 min_score 이상만 통과시킨다.

    Returns:
        (passed_outfits, stats)
    """
    cache = load_cache()
    passed = []
    stats = {"total": len(outfits), "evaluated": 0, "cached": 0,
             "passed": 0, "failed": 0, "skipped": 0}

    for i, outfit in enumerate(outfits):
        oid = outfit.get("outfit_id", f"outfit_{i}")

        # 캐시 확인
        if oid in cache:
            score_data = cache[oid]
            stats["cached"] += 1
        elif dry_run:
            # dry-run: 규칙 기반 간이 점수
            score_data = _rule_based_score(outfit)
            stats["evaluated"] += 1
        elif GEMINI_API_KEY:
            # Gemini 평가
            score_data = evaluate_single(outfit)
            if score_data:
                cache[oid] = score_data
                stats["evaluated"] += 1
            else:
                stats["skipped"] += 1
                continue

            # Rate limit 방지
            if (i + 1) % MAX_CONCURRENT == 0:
                time.sleep(1)
        else:
            # API 키 없으면 규칙 기반
            score_data = _rule_based_score(outfit)
            stats["evaluated"] += 1

        weighted = calculate_weighted_score(score_data)
        outfit["llm_quality_score"] = round(weighted)
        outfit["eval_detail"] = score_data

        if weighted >= min_score:
            passed.append(outfit)
            stats["passed"] += 1
        else:
            stats["failed"] += 1

        if (i + 1) % 100 == 0:
            logger.info("진행: %d/%d (통과: %d)", i + 1, stats["total"], stats["passed"])

    save_cache(cache)
    return passed, stats


def _rule_based_score(outfit: dict) -> dict:
    """Gemini 없이 규칙 기반 간이 점수를 산출한다."""
    items = outfit.get("items", [])

    # 스타일 통일감: 포멀도 편차가 작으면 높음
    formalities = [i.get("formality", 3) for i in items]
    if formalities:
        f_std = (max(formalities) - min(formalities))
        style_cohesion = max(1, 5 - f_std)
    else:
        style_cohesion = 3

    # 아이템 수가 적절하면(3~4개) 높음
    n_items = len(items)
    silhouette = 4 if 3 <= n_items <= 4 else 3

    return {
        "style_cohesion": style_cohesion,
        "silhouette_balance": silhouette,
        "trend_relevance": 3,
        "material_harmony": 3,
        "overall_styling": 3,
        "comment": "규칙 기반 간이 평가",
    }


# ── 메인 ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Gemini 코디 품질 평가")
    parser.add_argument("--min-score", type=int, default=3, help="최소 통과 점수 (기본 3)")
    parser.add_argument("--dry-run", action="store_true", help="Gemini 없이 규칙 기반 평가")
    parser.add_argument("--input", type=str, default=str(OUTFITS_PATH), help="입력 파일")
    parser.add_argument("--output", type=str, default=str(EVALUATED_PATH), help="출력 파일")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error("입력 파일 없음: %s", input_path)
        return

    with open(input_path, "r", encoding="utf-8") as f:
        outfits = json.load(f)

    logger.info("평가 시작: %d개 코디 (min_score=%d, dry_run=%s)",
                len(outfits), args.min_score, args.dry_run)

    passed, stats = evaluate_batch(outfits, min_score=args.min_score, dry_run=args.dry_run)

    output_path = Path(args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(passed, f, ensure_ascii=False, indent=2)

    logger.info("평가 완료: %s", json.dumps(stats, ensure_ascii=False))
    logger.info("통과 코디 %d개 → %s", len(passed), output_path)


if __name__ == "__main__":
    main()
