"""여성 코디 이미지 — 네이버 API 여성 전용 수집 + 라운드로빈."""

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

MALE_KW = {"남성", "남자", "맨즈", "mens"}

FEMALE_MUST_KW = {"여성", "여자", "우먼", "women", "woman"}

FEMALE_QUERIES = {
    "블라우스": [
        "여성 블라우스", "여성 쉬폰 블라우스", "여성 리본 블라우스",
        "여성 오피스 블라우스", "여자 블라우스",
    ],
    "스커트": [
        "여성 미디 스커트", "여성 A라인 스커트", "여성 플리츠 스커트",
        "여자 롱스커트", "여성 오피스 스커트",
    ],
    "원피스": [
        "여성 원피스", "여성 플로럴 원피스", "여자 미디 원피스",
        "여성 캐주얼 원피스", "여성 셔츠 원피스",
    ],
    "힐": [
        "여성 힐", "여성 펌프스", "여성 미들힐", "여자 구두",
        "여성 스틸레토", "여성 청키힐",
    ],
    "니트": [
        "여성 니트", "여자 라운드 니트", "여성 브이넥 니트",
        "여성 캐시미어 니트", "여성 크롭 니트",
    ],
    "셔츠": [
        "여성 셔츠", "여자 오버핏 셔츠", "여성 린넨 셔츠",
        "여성 캐주얼 셔츠", "여성 스트라이프 셔츠",
    ],
    "슬랙스": [
        "여성 슬랙스", "여자 와이드 슬랙스", "여성 정장 슬랙스",
        "여성 9부 슬랙스", "여성 일자 슬랙스",
    ],
    "자켓": [
        "여성 자켓", "여자 블레이저", "여성 트위드 자켓",
        "여성 크롭 자켓", "여성 캐주얼 자켓",
    ],
    "청바지": [
        "여성 청바지", "여자 와이드 데님", "여성 슬림 청바지",
        "여성 일자 청바지", "여성 부츠컷 청바지",
    ],
    "스니커즈": [
        "여성 스니커즈", "여자 운동화", "여성 캐주얼 스니커즈",
        "여성 흰 운동화", "여성 러닝화",
    ],
    "티셔츠": [
        "여성 반팔 티셔츠", "여자 라운드 티셔츠",
        "여성 캐주얼 티셔츠", "여성 크롭 티셔츠",
    ],
    "맨투맨": [
        "여성 맨투맨", "여자 오버핏 맨투맨", "여성 기모 맨투맨",
        "여성 캐주얼 맨투맨",
    ],
    "후드": [
        "여성 후드티", "여자 후드 집업", "여성 오버핏 후드",
        "여성 캐주얼 후드티",
    ],
    "코트": [
        "여성 코트", "여자 롱코트", "여성 트렌치코트",
        "여성 울 코트", "여성 핸드메이드 코트",
    ],
    "플랫슈즈": [
        "여성 플랫슈즈", "여자 플랫슈즈", "여성 발레슈즈",
        "여성 로퍼 플랫",
    ],
    "로퍼": [
        "여성 로퍼", "여자 페니로퍼", "여성 캐주얼 로퍼",
    ],
    "가디건": [
        "여성 가디건", "여자 니트 가디건", "여성 봄 가디건",
    ],
    "카디건": [
        "여성 카디건", "여자 카디건",
    ],
    "반바지": [
        "여성 반바지", "여자 숏팬츠", "여성 데님 반바지",
    ],
    "바람막이": [
        "여성 바람막이", "여자 윈드브레이커",
    ],
    "크롭탑": [
        "여성 크롭탑", "여자 크롭 티셔츠",
    ],
    "조거팬츠": [
        "여성 조거팬츠", "여자 트레이닝 바지",
    ],
    "모자": [
        "여성 버킷햇", "여자 볼캡", "여성 벙거지",
    ],
    "패딩": [
        "여성 패딩", "여자 숏패딩", "여성 경량 패딩",
    ],
    "반팔티": [
        "여성 반팔티", "여자 반팔 티셔츠",
    ],
}


def search_naver(query, display=30):
    if not NAVER_ID:
        return []
    url = "https://openapi.naver.com/v1/search/shop.json"
    headers = {"X-Naver-Client-Id": NAVER_ID, "X-Naver-Client-Secret": NAVER_SECRET}
    try:
        r = httpx.get(url, headers=headers, params={"query": query, "display": display, "sort": "sim"}, timeout=10)
        return r.json().get("items", []) if r.status_code == 200 else []
    except Exception:
        return []


def clean_title(t):
    return re.sub(r"<[^>]+>", "", t).strip()


def is_confirmed_female(title, item_raw):
    t = title.lower()
    if any(kw in t for kw in FEMALE_MUST_KW):
        return True
    for field in ("category1", "category2", "category3", "category4"):
        if "여성" in item_raw.get(field, ""):
            return True
    return False


def main():
    print("=" * 60)
    print("여성 코디 이미지 전면 교체")
    print("=" * 60)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(DATA_DIR / "outfits_scored.json", DATA_DIR / f"outfits_scored_backup_{ts}.json")

    # 1. 수집
    print("\n[1] 여성 상품 수집")
    pool = {}
    total = 0
    for cat, queries in FEMALE_QUERIES.items():
        seen = set()
        products = []
        for query in queries:
            items = search_naver(query, 30)
            for item in items:
                img = item.get("image", "")
                if not img or img in seen:
                    continue
                title = clean_title(item.get("title", ""))
                if any(kw in title.lower() for kw in MALE_KW):
                    continue
                if not is_confirmed_female(title, item):
                    continue
                seen.add(img)
                products.append({
                    "title": title, "image_url": img,
                    "price": int(item.get("lprice", 0)),
                    "brand": item.get("brand", item.get("mallName", "")),
                    "gender": "female",
                })
            time.sleep(0.12)
        pool[cat] = products
        print(f"  {cat:15s}: {len(products)}개")
        total += len(products)
    print(f"  총: {total}개")

    pool_path = DATA_DIR / "female_products_full.json"
    pool_path.write_text(json.dumps(pool, ensure_ascii=False, indent=2), encoding="utf-8")

    # workout 풀 female도 통합
    wp_path = DATA_DIR / "workout_products.json"
    if wp_path.exists():
        wp = json.loads(wp_path.read_text(encoding="utf-8"))
        for cat, items in wp.items():
            female_items = [it for it in items if it.get("gender") == "female"]
            if cat not in pool:
                pool[cat] = []
            existing = {p["image_url"] for p in pool[cat]}
            for it in female_items:
                if it["image_url"] not in existing:
                    pool[cat].append(it)

    # 2. 라운드로빈 큐
    print("\n[2] 큐 구축")
    queues = {}
    for cat, items in pool.items():
        imgs = list({it["image_url"]: it for it in items}.values())
        random.shuffle(imgs)
        queues[cat] = imgs
        if imgs:
            print(f"  {cat:15s}: {len(imgs)}개")

    FALLBACK = {"카디건": "니트", "가디건": "니트", "크롭탑": "티셔츠",
                "패딩": "자켓", "벨트": "스카프"}

    # 3. 교체
    print("\n[3] 이미지 교체")
    outfits = json.loads((DATA_DIR / "outfits_scored.json").read_text(encoding="utf-8"))
    q_idx = defaultdict(int)
    replaced = 0
    no_pool = 0

    for o in outfits:
        if o.get("gender") != "female":
            continue
        tpos = [t.lower() for t in (o.get("designed_tpo") or [])]
        if "workout" in tpos:
            continue
        for it in o.get("items", []):
            cat = it.get("category", "")
            q = queues.get(cat) or queues.get(FALLBACK.get(cat, ""), [])
            if not q:
                no_pool += 1
                continue
            idx = q_idx[cat] % len(q)
            chosen = q[idx]
            q_idx[cat] = idx + 1
            it["image_url"] = chosen["image_url"]
            if chosen.get("title"):
                it["title"] = chosen["title"]
            if chosen.get("brand"):
                it["brand"] = chosen["brand"]
            if chosen.get("price"):
                it["price"] = chosen["price"]
            replaced += 1

    print(f"  교체: {replaced}개, 풀없음: {no_pool}개")
    (DATA_DIR / "outfits_scored.json").write_text(
        json.dumps(outfits, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 4. 검증
    print(f"\n{'=' * 60}")
    print("검증")
    pool_imgs = set()
    for cat, items in pool.items():
        for it in items:
            pool_imgs.add(it["image_url"])

    female_nw = [o for o in outfits if o.get("gender") == "female"
                 and not (o.get("designed_tpo") and "workout" in [t.lower() for t in o["designed_tpo"]])]
    total_items = sum(len(o.get("items", [])) for o in female_nw)
    fresh = sum(1 for o in female_nw for it in o.get("items", [])
                if it.get("image_url", "").strip() in pool_imgs)
    print(f"여성 비-workout: {len(female_nw)}개 코디, {total_items}개 아이템")
    print(f"신규 여성 이미지: {fresh}/{total_items} ({fresh / total_items * 100:.1f}%)")


if __name__ == "__main__":
    main()
