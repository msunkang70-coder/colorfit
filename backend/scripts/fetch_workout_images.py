"""운동복 전용 상품 이미지 수집 + workout 코디에 매칭.

네이버 쇼핑 API로 운동/스포츠 아이템을 카테고리별로 수집하고,
workout TPO 코디의 아이템 이미지를 교체한다.
"""

import json
import os
import time
import random
import re
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from urllib.parse import quote

import httpx

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Naver API
NAVER_ID = os.environ.get("NAVER_CLIENT_ID", "")
NAVER_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")

# .env fallback
if not NAVER_ID:
    env_path = DATA_DIR.parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("NAVER_CLIENT_ID="):
                NAVER_ID = line.split("=", 1)[1].strip()
            elif line.startswith("NAVER_CLIENT_SECRET="):
                NAVER_SECRET = line.split("=", 1)[1].strip()

# 카테고리별 검색 쿼리 (남성/여성/공용)
WORKOUT_QUERIES = {
    "스니커즈": ["남성 운동화", "러닝화 남성", "운동화 여성", "스포츠 스니커즈"],
    "맨투맨": ["남성 스포츠 맨투맨", "트레이닝 맨투맨 남성", "여성 운동 맨투맨"],
    "후드": ["남성 스포츠 후드", "트레이닝 후드집업 남성", "여성 운동 후드"],
    "조거팬츠": ["남성 조거팬츠", "트레이닝 팬츠 남성", "여성 조거팬츠"],
    "레깅스": ["여성 운동 레깅스", "스포츠 레깅스", "요가 레깅스"],
    "반팔티": ["남성 스포츠 반팔", "드라이핏 반팔 남성", "여성 운동 반팔"],
    "티셔츠": ["남성 스포츠 티셔츠", "남성 드라이핏 티셔츠", "남성 운동 반팔티", "여성 스포츠 티셔츠"],
    "반바지": ["남성 스포츠 반바지", "트레이닝 숏팬츠 남성", "여성 운동 반바지"],
    "바람막이": ["남성 바람막이", "스포츠 바람막이", "러닝 자켓"],
    "스포츠브라": ["여성 스포츠브라", "운동 브라탑"],
    "트레이닝팬츠": ["남성 트레이닝팬츠", "운동 트레이닝 남성"],
    "모자": ["남성 스포츠 캡모자", "남성 러닝 캡", "여성 스포츠 캡", "나이키 남성 볼캡"],
    "크롭탑": ["여성 운동 크롭탑", "여성 스포츠 크롭탑"],
}

GENDER_MAP = {
    "남성": "male",
    "여성": "female",
    "나이키 남성": "male",
}


def search_naver(query: str, display: int = 20) -> list[dict]:
    """네이버 쇼핑 API 검색."""
    if not NAVER_ID:
        print("  WARNING: Naver API 키 없음")
        return []

    url = "https://openapi.naver.com/v1/search/shop.json"
    headers = {
        "X-Naver-Client-Id": NAVER_ID,
        "X-Naver-Client-Secret": NAVER_SECRET,
    }
    params = {"query": query, "display": display, "sort": "sim"}

    try:
        r = httpx.get(url, headers=headers, params=params, timeout=10)
        if r.status_code == 200:
            return r.json().get("items", [])
        else:
            print(f"  API error {r.status_code}: {query}")
            return []
    except Exception as e:
        print(f"  API exception: {e}")
        return []


def clean_title(title: str) -> str:
    """HTML 태그 제거."""
    return re.sub(r"<[^>]+>", "", title).strip()


def infer_gender(query: str) -> str:
    """쿼리에서 성별 추론."""
    for keyword, gender in GENDER_MAP.items():
        if keyword in query:
            return gender
    return "unisex"


def collect_workout_products() -> dict[str, list[dict]]:
    """카테고리별 운동 상품 수집."""
    pool = defaultdict(list)  # category -> [product]
    total = 0

    for category, queries in WORKOUT_QUERIES.items():
        cat_products = []
        for query in queries:
            items = search_naver(query, display=20)
            gender = infer_gender(query)

            for item in items:
                img = item.get("image", "")
                if not img:
                    continue

                product = {
                    "product_id": item.get("productId", ""),
                    "title": clean_title(item.get("title", "")),
                    "category": category,
                    "image_url": img,
                    "price": int(item.get("lprice", 0)),
                    "brand": item.get("brand", item.get("mallName", "")),
                    "gender": gender,
                }
                cat_products.append(product)

            time.sleep(0.15)  # rate limit

        # 중복 제거
        seen = set()
        for p in cat_products:
            key = p["image_url"]
            if key not in seen:
                seen.add(key)
                pool[category].append(p)

        print(f"  {category}: {len(pool[category])}개 수집")
        total += len(pool[category])

    print(f"  총 수집: {total}개")
    return pool


FEMALE_KEYWORDS = ["여성", "우먼", "women", "woman", "레이디", "걸즈", "girls",
                    "브라탑", "스포츠브라", "요가", "필라테스", "레깅스"]
MALE_KEYWORDS = ["남성", "남자", "men's", "맨즈"]

# 타이틀에 성별 키워드 없지만 실제로 남성 전용으로 판단 가능한 키워드
MALE_STRONG_KEYWORDS = ["남성", "남자", "맨즈", "men"]
FEMALE_STRONG_KEYWORDS = ["여성", "여자", "우먼", "women", "레이디"]


def _title_gender_ok(title: str, target_gender: str) -> bool:
    """타이틀에 반대 성별 키워드가 있으면 False."""
    t = title.lower()
    if target_gender == "male":
        return not any(kw in t for kw in FEMALE_KEYWORDS)
    elif target_gender == "female":
        return not any(kw in t for kw in MALE_KEYWORDS)
    return True


def _has_strong_gender_signal(title: str, target_gender: str) -> bool:
    """타이틀에 해당 성별을 명시적으로 나타내는 키워드가 있는지."""
    t = title.lower()
    if target_gender == "male":
        return any(kw in t for kw in MALE_STRONG_KEYWORDS)
    elif target_gender == "female":
        return any(kw in t for kw in FEMALE_STRONG_KEYWORDS)
    return False


def _build_gender_pools(candidates: list[dict], gender: str) -> list[list[dict]]:
    """성별 기준으로 후보를 우선순위별 풀로 분리 (3단계).

    1순위: 정확한 성별 태그 + 타이틀에 해당 성별 명시
    2순위: 정확한 성별 태그 + 반대 성별 키워드 없음
    3순위: unisex + 반대 성별 키워드 없음
    """
    tier1 = []  # 성별 태그 일치 + 타이틀에 명시적 성별 신호
    tier2 = []  # 성별 태그 일치 + 타이틀 안전
    tier3 = []  # unisex + 타이틀 안전

    for p in candidates:
        if not _title_gender_ok(p["title"], gender):
            continue  # 반대 성별 키워드 → 제외

        if p["gender"] == gender:
            if _has_strong_gender_signal(p["title"], gender):
                tier1.append(p)
            else:
                tier2.append(p)
        elif p["gender"] == "unisex":
            tier3.append(p)

    return [tier1, tier2, tier3]


def match_workout_images(outfits: list[dict], pool: dict[str, list[dict]]) -> int:
    """workout 코디의 아이템 이미지를 운동복 풀에서 교체.

    라운드로빈: 카테고리×성별별로 셔플된 리스트를 순서대로 할당하여
    동일 이미지 반복을 최소화한다.
    """
    fixed = 0

    # 카테고리×성별별 라운드로빈 큐 구축
    queues: dict[tuple[str, str], list[dict]] = {}  # (cat, gender) -> shuffled list
    queue_idx: dict[tuple[str, str], int] = {}

    for o in outfits:
        tpos = [t.lower() for t in (o.get("designed_tpo") or [])]
        if "workout" not in tpos:
            continue

        gender = o.get("gender", "")

        for item in o.get("items", []):
            cat = item.get("category", "")
            candidates = pool.get(cat, [])

            if not candidates:
                continue

            key = (cat, gender)
            if key not in queues:
                # 우선순위별 풀 구축 → 합쳐서 셔플
                tiers = _build_gender_pools(candidates, gender)
                # tier1 먼저, tier2, tier3 순으로 합침
                combined = []
                for tier in tiers:
                    shuffled = list(tier)
                    random.shuffle(shuffled)
                    combined.extend(shuffled)

                if not combined:
                    # fallback: 전체 후보
                    combined = list(candidates)
                    random.shuffle(combined)

                queues[key] = combined
                queue_idx[key] = 0

            # 라운드로빈 할당
            q = queues[key]
            idx = queue_idx[key] % len(q)
            chosen = q[idx]
            queue_idx[key] = idx + 1

            # 이미지 교체
            item["image_url"] = chosen["image_url"]
            item["title"] = chosen["title"]
            item["brand"] = chosen.get("brand", "")
            if chosen.get("price"):
                item["price"] = chosen["price"]
            fixed += 1

    return fixed


def main():
    import sys
    rematch_only = "--rematch" in sys.argv

    print("=" * 60)
    print("운동복 전용 이미지 수집 + 매칭")
    print("=" * 60)

    # 백업
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(DATA_DIR / "outfits_scored.json", DATA_DIR / f"outfits_scored_backup_{ts}.json")

    pool_path = DATA_DIR / "workout_products.json"

    if rematch_only and pool_path.exists():
        # 기존 풀 재사용 (API 호출 없이 재매핑)
        print("\n[1] 기존 풀 재사용 (--rematch)")
        pool = json.loads(pool_path.read_text(encoding="utf-8"))
        total = sum(len(v) for v in pool.values())
        print(f"  기존 풀: {total}개")
    else:
        # 네이버 API 수집
        print("\n[1] 네이버 쇼핑 API 수집")
        pool = collect_workout_products()
        pool_data = {cat: items for cat, items in pool.items()}
        pool_path.write_text(json.dumps(pool_data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  저장: {pool_path.name}")

    # 2. workout 코디 이미지 교체
    print("\n[2] Workout 코디 이미지 교체")
    outfits = json.loads((DATA_DIR / "outfits_scored.json").read_text(encoding="utf-8"))

    fixed = match_workout_images(outfits, pool)
    print(f"  교체: {fixed}개 아이템")

    # 저장
    (DATA_DIR / "outfits_scored.json").write_text(
        json.dumps(outfits, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 3. 검증
    print(f"\n{'='*60}")
    print("검증")
    print(f"{'='*60}")

    workout = [o for o in outfits
               if o.get("designed_tpo") and "workout" in [t.lower() for t in o["designed_tpo"]]
               and o.get("scores")]

    for gender in ["female", "male"]:
        wg = [o for o in workout if o.get("gender") == gender]
        img_count = sum(1 for o in wg if all(
            it.get("image_url", "").strip() for it in o.get("items", [])
        ))
        print(f"\n  workout {gender}: {len(wg)}개, 전체 이미지: {img_count}/{len(wg)}")
        for i, o in enumerate(wg[:3]):
            cats = [it.get("category", "?") for it in o.get("items", [])]
            titles = [it.get("title", "")[:20] for it in o.get("items", [])]
            print(f"    #{i+1} {cats}")
            for j, it in enumerate(o.get("items", [])):
                print(f"       {it.get('category','?')}: {it.get('title','')[:30]} | {it.get('image_url','')[:50]}")


if __name__ == "__main__":
    random.seed(42)
    main()
