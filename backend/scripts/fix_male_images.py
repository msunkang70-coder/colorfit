"""남성 코디에서 여성 이미지를 남성 이미지로 완전 교체.

문제: normalized 풀의 일부 카테고리(티셔츠, 조거팬츠 등)에 male 이미지가 0개
→ fix_gender_and_images.py가 female 이미지를 남성 코디에 매핑

해결:
1. 네이버 쇼핑 API로 부족한 카테고리의 남성 상품 수집
2. normalized 풀 + workout 풀 + 신규 수집 풀 통합
3. 남성 코디의 female-origin 이미지를 모두 male 이미지로 교체
"""

import json
import os
import re
import time
import random
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict

import httpx

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
random.seed(42)

# Naver API
NAVER_ID = os.environ.get("NAVER_CLIENT_ID", "")
NAVER_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")

if not NAVER_ID:
    env_path = DATA_DIR.parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("NAVER_CLIENT_ID="):
                NAVER_ID = line.split("=", 1)[1].strip()
            elif line.startswith("NAVER_CLIENT_SECRET="):
                NAVER_SECRET = line.split("=", 1)[1].strip()

# 남성 전용 검색 쿼리 (부족한 카테고리)
MALE_QUERIES = {
    "티셔츠": ["남성 반팔 티셔츠", "남성 라운드 티셔츠", "남성 캐주얼 티셔츠",
               "남성 무지 티셔츠", "남성 면 티셔츠"],
    "조거팬츠": ["남성 조거팬츠", "남성 트레이닝 바지", "남성 카고 조거팬츠",
                "남성 스웨트팬츠"],
    "맨투맨": ["남성 맨투맨", "남성 기모 맨투맨", "남성 캐주얼 맨투맨",
              "남성 오버핏 맨투맨"],
    "후드": ["남성 후드티", "남성 후드 집업", "남성 캐주얼 후드"],
    "청바지": ["남성 청바지", "남성 데님 팬츠", "남성 슬림 진"],
    "반바지": ["남성 반바지", "남성 캐주얼 숏팬츠", "남성 면 반바지"],
    "셔츠": ["남성 캐주얼 셔츠", "남성 옥스퍼드 셔츠", "남성 린넨 셔츠"],
    "슬랙스": ["남성 슬랙스", "남성 와이드 슬랙스", "남성 정장 바지"],
    "니트": ["남성 니트", "남성 라운드 니트", "남성 캐주얼 니트"],
    "바람막이": ["남성 바람막이", "남성 윈드브레이커"],
}


def search_naver(query: str, display: int = 20) -> list[dict]:
    if not NAVER_ID:
        return []
    url = "https://openapi.naver.com/v1/search/shop.json"
    headers = {"X-Naver-Client-Id": NAVER_ID, "X-Naver-Client-Secret": NAVER_SECRET}
    params = {"query": query, "display": display, "sort": "sim"}
    try:
        r = httpx.get(url, headers=headers, params=params, timeout=10)
        return r.json().get("items", []) if r.status_code == 200 else []
    except Exception:
        return []


def clean_title(title: str) -> str:
    return re.sub(r"<[^>]+>", "", title).strip()


FEMALE_KW = {"여성", "우먼", "women", "woman", "레이디", "걸즈", "girls",
             "브라탑", "스포츠브라", "요가", "필라테스", "레깅스",
             "원피스", "블라우스", "스커트"}


def collect_male_products() -> dict[str, list[dict]]:
    """네이버 API로 남성 전용 상품 수집."""
    pool = defaultdict(list)
    total = 0

    for category, queries in MALE_QUERIES.items():
        seen = set()
        for query in queries:
            items = search_naver(query, display=20)
            for item in items:
                img = item.get("image", "")
                if not img or img in seen:
                    continue
                title = clean_title(item.get("title", ""))
                # 여성 키워드 필터
                if any(kw in title.lower() for kw in FEMALE_KW):
                    continue
                seen.add(img)
                pool[category].append({
                    "product_id": item.get("productId", ""),
                    "title": title,
                    "category": category,
                    "image_url": img,
                    "price": int(item.get("lprice", 0)),
                    "brand": item.get("brand", item.get("mallName", "")),
                    "gender": "male",
                })
            time.sleep(0.15)

        print(f"  {category}: {len(pool[category])}개")
        total += len(pool[category])

    print(f"  총: {total}개")
    return pool


def build_norm_gender_map() -> dict[str, str]:
    """normalized 풀 이미지 → 성별 매핑."""
    img_gender = {}
    norm_dir = DATA_DIR / "normalized"
    if norm_dir.exists():
        for f in norm_dir.glob("*.json"):
            items = json.loads(f.read_text(encoding="utf-8"))
            for it in items:
                img = it.get("image_url", "").strip()
                if img:
                    img_gender[img] = it.get("gender", "unisex")
    return img_gender


def build_male_image_pool(new_pool, workout_pool_path) -> dict[str, list[str]]:
    """모든 소스에서 남성 전용 이미지 풀 구축. cat → [image_url]"""
    pool = defaultdict(list)

    # 1. 새로 수집한 남성 상품
    for cat, items in new_pool.items():
        for it in items:
            pool[cat].append(it["image_url"])

    # 2. workout 상품 풀 (male만)
    if workout_pool_path.exists():
        wp = json.loads(workout_pool_path.read_text(encoding="utf-8"))
        for cat, items in wp.items():
            for it in items:
                if it.get("gender") == "male":
                    pool[cat].append(it["image_url"])

    # 3. normalized 풀 (male/unisex)
    norm_dir = DATA_DIR / "normalized"
    if norm_dir.exists():
        for f in norm_dir.glob("*.json"):
            items = json.loads(f.read_text(encoding="utf-8"))
            for it in items:
                img = it.get("image_url", "").strip()
                cat = it.get("category", "")
                g = it.get("gender", "unisex")
                if img and cat and g in ("male", "unisex"):
                    # unisex 중 여성 키워드 제외
                    title = it.get("title", it.get("name", "")).lower()
                    if not any(kw in title for kw in FEMALE_KW):
                        pool[cat].append(img)

    # 4. 기존 코디에서 male 이미지 (확실한 것만)
    outfits = json.loads((DATA_DIR / "outfits_scored.json").read_text(encoding="utf-8"))
    norm_gender = build_norm_gender_map()
    for o in outfits:
        if o.get("gender") != "male":
            continue
        for it in o.get("items", []):
            img = it.get("image_url", "").strip()
            cat = it.get("category", "")
            if img and cat and norm_gender.get(img, "male") != "female":
                pool[cat].append(img)

    # 중복 제거 + 셔플
    for cat in pool:
        pool[cat] = list(set(pool[cat]))
        random.shuffle(pool[cat])

    return pool


def main():
    print("=" * 60)
    print("남성 코디 여성 이미지 완전 교체")
    print("=" * 60)

    # 백업
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(DATA_DIR / "outfits_scored.json", DATA_DIR / f"outfits_scored_backup_{ts}.json")

    # 1. 남성 상품 수집
    print("\n[1] 네이버 API 남성 상품 수집")
    new_pool = collect_male_products()

    # 수집 결과 저장
    pool_path = DATA_DIR / "male_products.json"
    pool_path.write_text(json.dumps(new_pool, ensure_ascii=False, indent=2), encoding="utf-8")

    # 2. 통합 남성 이미지 풀
    print("\n[2] 통합 남성 이미지 풀 구축")
    male_pool = build_male_image_pool(new_pool, DATA_DIR / "workout_products.json")
    for cat in sorted(male_pool.keys()):
        print(f"  {cat:15s}: {len(male_pool[cat])}개")

    # 3. female 이미지 교체
    print("\n[3] 여성 이미지 교체")
    norm_gender = build_norm_gender_map()
    outfits = json.loads((DATA_DIR / "outfits_scored.json").read_text(encoding="utf-8"))

    replaced = 0
    still_female = 0
    queue_idx = defaultdict(int)  # 라운드로빈용

    for o in outfits:
        if o.get("gender") != "male":
            continue

        for it in o.get("items", []):
            img = it.get("image_url", "").strip()
            if not img:
                continue

            # 이미지 원본이 female인 경우에만 교체
            orig_gender = norm_gender.get(img, "unknown")
            if orig_gender != "female":
                continue

            cat = it.get("category", "")
            candidates = male_pool.get(cat, [])

            if candidates:
                idx = queue_idx[cat] % len(candidates)
                it["image_url"] = candidates[idx]
                queue_idx[cat] = idx + 1
                replaced += 1
            else:
                still_female += 1

    print(f"  교체: {replaced}개")
    print(f"  미교체: {still_female}개")

    # 저장
    (DATA_DIR / "outfits_scored.json").write_text(
        json.dumps(outfits, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 4. 검증
    print(f"\n{'=' * 60}")
    print("검증")
    print(f"{'=' * 60}")

    male_outfits = [o for o in outfits if o.get("gender") == "male"]
    female_in_male = 0
    for o in male_outfits:
        for it in o.get("items", []):
            img = it.get("image_url", "").strip()
            if img and norm_gender.get(img) == "female":
                female_in_male += 1

    total_male_items = sum(len(o.get("items", [])) for o in male_outfits)
    print(f"남성 코디: {len(male_outfits)}개, 아이템: {total_male_items}개")
    print(f"female 이미지 잔존: {female_in_male}개 (목표 0)")


if __name__ == "__main__":
    main()
