"""
curate_by_tone.py — 12톤별 네이버 쇼핑 API 수집 스크립트

사용법:
    # 단일 톤 수집
    python -m backend.scripts.curate_by_tone --tone spring_warm_light

    # 전체 12톤 순차 수집
    python -m backend.scripts.curate_by_tone --all

    # 4톤 병렬 수집 (터미널 4개)
    python -m backend.scripts.curate_by_tone --tone spring_warm_light &
    python -m backend.scripts.curate_by_tone --tone spring_warm_bright &
    python -m backend.scripts.curate_by_tone --tone spring_warm_mute &
    python -m backend.scripts.curate_by_tone --tone summer_cool_light &
"""

import argparse
import json
import logging
import os
import time
from pathlib import Path
from urllib.parse import quote

import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "backend" / "data"
RAW_DIR = DATA_DIR / "raw"
QUERIES_PATH = DATA_DIR / "tone_queries.json"

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")

SEARCH_URL = "https://openapi.naver.com/v1/search/shop.json"

ALL_TONES = [
    "spring_warm_light", "spring_warm_bright", "spring_warm_mute",
    "summer_cool_light", "summer_cool_soft", "summer_cool_mute",
    "autumn_warm_deep", "autumn_warm_mute", "autumn_warm_bright",
    "winter_cool_deep", "winter_cool_bright", "winter_cool_light",
]


def search_products(query: str, display: int = 100, start: int = 1) -> dict | None:
    """네이버 쇼핑 API 호출. Rate limit 시 exponential backoff 재시도."""
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        raise RuntimeError(
            "NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 환경변수가 설정되지 않았습니다. "
            ".env 파일을 확인하세요."
        )

    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {
        "query": query,
        "display": min(display, 100),
        "start": start,
        "sort": "sim",
    }

    max_retries = 5
    backoff = 1.0

    for attempt in range(max_retries):
        try:
            resp = requests.get(SEARCH_URL, headers=headers, params=params, timeout=10)

            if resp.status_code == 200:
                return resp.json()

            if resp.status_code == 429:
                logger.warning(
                    "Rate limit 도달 (429). %.1f초 후 재시도 (%d/%d)",
                    backoff, attempt + 1, max_retries,
                )
                time.sleep(backoff)
                backoff *= 2
                continue

            logger.error(
                "API 에러: status=%d, body=%s", resp.status_code, resp.text[:200]
            )
            return None

        except requests.exceptions.Timeout:
            logger.warning("타임아웃. %.1f초 후 재시도 (%d/%d)", backoff, attempt + 1, max_retries)
            time.sleep(backoff)
            backoff *= 2
        except requests.exceptions.RequestException as e:
            logger.error("요청 실패: %s", e)
            return None

    logger.error("최대 재시도 횟수(%d) 초과: query=%s", max_retries, query)
    return None


def collect_for_query(query: str, max_items: int = 300) -> list[dict]:
    """단일 키워드에 대해 페이징하며 상품을 수집한다."""
    items = []
    start = 1

    while len(items) < max_items and start <= 1000:
        display = min(100, max_items - len(items))
        result = search_products(query, display=display, start=start)

        if result is None:
            break

        batch = result.get("items", [])
        if not batch:
            break

        items.extend(batch)
        start += display

        # API 호출 간격 (rate limit 예방)
        time.sleep(0.15)

    return items


def collect_for_tone(tone_id: str, queries: list[str]) -> list[dict]:
    """특정 톤의 모든 키워드에 대해 수집하고 raw JSON으로 저장한다."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    all_items = []
    seen_ids = set()

    for i, query in enumerate(queries, 1):
        logger.info("[%s] 쿼리 %d/%d: %s", tone_id, i, len(queries), query)
        items = collect_for_query(query)

        # 중복 제거 (productId 기준)
        new_items = []
        for item in items:
            pid = item.get("productId", "")
            if pid and pid not in seen_ids:
                seen_ids.add(pid)
                item["_query"] = query
                item["_tone_id"] = tone_id
                new_items.append(item)

        all_items.extend(new_items)
        logger.info(
            "[%s] +%d개 (중복 제외), 누적 %d개",
            tone_id, len(new_items), len(all_items),
        )

    # raw JSON 저장
    output_path = RAW_DIR / f"{tone_id}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {"tone_id": tone_id, "total": len(all_items), "items": all_items},
            f,
            ensure_ascii=False,
            indent=2,
        )

    logger.info("[%s] 수집 완료: %d개 → %s", tone_id, len(all_items), output_path)
    return all_items


def load_queries() -> dict[str, list[str]]:
    """tone_queries.json에서 톤별 키워드를 로드한다."""
    if not QUERIES_PATH.exists():
        raise FileNotFoundError(
            f"톤별 키워드 파일이 없습니다: {QUERIES_PATH}\n"
            "Task 1.4를 먼저 실행하세요."
        )
    with open(QUERIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="12톤별 네이버 쇼핑 API 수집")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--tone", type=str, choices=ALL_TONES, help="수집할 톤 ID")
    group.add_argument("--all", action="store_true", help="전체 12톤 순차 수집")
    parser.add_argument(
        "--dry-run", action="store_true", help="API 호출 없이 키워드만 확인"
    )
    args = parser.parse_args()

    queries = load_queries()

    tones = ALL_TONES if args.all else [args.tone]

    for tone_id in tones:
        tone_queries = queries.get(tone_id, [])
        if not tone_queries:
            logger.warning("[%s] 키워드가 없습니다. 건너뜁니다.", tone_id)
            continue

        logger.info("[%s] 키워드 %d개로 수집 시작", tone_id, len(tone_queries))

        if args.dry_run:
            for q in tone_queries:
                print(f"  {q}")
            continue

        collect_for_tone(tone_id, tone_queries)

    logger.info("완료.")


if __name__ == "__main__":
    main()
