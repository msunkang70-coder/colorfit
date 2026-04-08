"""남성 코디 이미지 전면 교체 — 네이버 API 남성 전용 수집 + 라운드로빈.

문제: normalized 풀의 male/unisex 태깅이 부정확 → 여성 이미지 혼입 + 다양성 부족
해결: 전 카테고리 남성 전용 상품 대량 수집 → 남성 코디 이미지 100% 교체
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

FEMALE_KW = {"여성", "우먼", "women", "woman", "레이디", "걸즈", "girls",
             "브라탑", "스포츠브라", "요가", "필라테스", "원피스", "블라우스",
             "스커트", "매니큐어", "네일", "화장품", "뷰티"}

# 카테고리별 남성 전용 검색 쿼리 (다양성 확보를 위해 쿼리 다수 배치)
MALE_QUERIES = {
    "셔츠": [
        "남성 옥스포드 셔츠", "남성 캐주얼 셔츠", "남성 린넨 셔츠",
        "남성 스트라이프 셔츠", "남성 화이트 셔츠", "남성 오버핏 셔츠",
    ],
    "슬랙스": [
        "남성 슬랙스", "남성 와이드 슬랙스", "남성 정장 슬랙스",
        "남성 면 슬랙스", "남성 스트레이트 슬랙스", "남성 9부 슬랙스",
    ],
    "청바지": [
        "남성 청바지", "남성 슬림핏 데님", "남성 와이드 청바지",
        "남성 일자 청바지", "남성 스트레이트 진", "남성 데님 팬츠",
    ],
    "스니커즈": [
        "남성 스니커즈", "남성 운동화", "남성 캐주얼 스니커즈",
        "남성 흰 운동화", "남성 가죽 스니커즈", "남성 러닝화",
    ],
    "니트": [
        "남성 라운드 니트", "남성 브이넥 니트", "남성 캐시미어 니트",
        "남성 울 니트", "남성 케이블 니트", "남성 캐주얼 니트",
    ],
    "자켓": [
        "남성 캐주얼 자켓", "남성 블레이저", "남성 봄 자켓",
        "남성 싱글 자켓", "남성 데님 자켓", "남성 스포츠 자켓",
    ],
    "코트": [
        "남성 코트", "남성 싱글 코트", "남성 더블 코트",
        "남성 울 코트", "남성 트렌치코트", "남성 오버코트",
    ],
    "후드": [
        "남성 후드티", "남성 기모 후드", "남성 오버핏 후드",
        "남성 후드 집업", "남성 캐주얼 후드티",
    ],
    "맨투맨": [
        "남성 맨투맨", "남성 기모 맨투맨", "남성 오버핏 맨투맨",
        "남성 무지 맨투맨", "남성 캐주얼 맨투맨",
    ],
    "티셔츠": [
        "남성 반팔 티셔츠", "남성 라운드 티셔츠", "남성 면 티셔츠",
        "남성 무지 티셔츠", "남성 캐주얼 반팔",
    ],
    "로퍼": [
        "남성 로퍼", "남성 캐주얼 로퍼", "남성 가죽 로퍼",
        "남성 페니로퍼", "남성 스웨이드 로퍼",
    ],
    "조거팬츠": [
        "남성 조거팬츠", "남성 트레이닝 바지", "남성 스웨트팬츠",
        "남성 카고 조거팬츠", "남성 스포츠 바지",
    ],
    "반바지": [
        "남성 반바지", "남성 숏팬츠", "남성 면 반바지",
        "남성 캐주얼 반바지", "남성 카고 반바지",
    ],
    "반팔티": [
        "남성 스포츠 반팔", "남성 드라이핏 반팔", "남성 기능성 반팔",
        "남성 쿨링 반팔", "남성 운동 반팔티",
    ],
    "바람막이": [
        "남성 바람막이", "남성 윈드브레이커", "남성 경량 자켓",
        "남성 스포츠 바람막이",
    ],
    "정장바지": [
        "남성 정장바지", "남성 수트 팬츠", "남성 슬림 정장바지",
        "남성 구김방지 정장바지",
    ],
    "모자": [
        "남성 볼캡", "남성 캡모자", "남성 스냅백",
        "남성 야구모자", "남성 스포츠 캡",
    ],
    "크로스백": [
        "남성 크로스백", "남성 미니 크로스백", "남성 캐주얼 가방",
    ],
    "넥타이": [
        "남성 넥타이", "남성 실크 넥타이", "남성 비즈니스 넥타이",
    ],
    "트레이닝팬츠": [
        "남성 트레이닝팬츠", "남성 운동 바지", "남성 나이키 트레이닝",
    ],
    "가디건": [
        "남성 가디건", "남성 니트 가디건", "남성 봄 가디건",
    ],
    "패딩": [
        "남성 패딩", "남성 경량 패딩", "남성 숏패딩",
    ],
    "카디건": [
        "남성 카디건", "남성 봄 카디건",
    ],
    "사이드백": [
        "남성 사이드백", "남성 숄더백",
    ],
}


def search_naver(query: str, display: int = 30) -> list[dict]:
    if not NAVER_ID:
        print("  WARNING: Naver API 키 없음")
        return []
    url = "https://openapi.naver.com/v1/search/shop.json"
    headers = {"X-Naver-Client-Id": NAVER_ID, "X-Naver-Client-Secret": NAVER_SECRET}
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
    return re.sub(r"<[^>]+>", "", title).strip()


MALE_MUST_KW = {"남성", "남자", "맨즈", "men's", "man", "mens"}


def _is_confirmed_male(title: str, item_raw: dict) -> bool:
    """타이틀 또는 카테고리에서 남성 확인. 하나라도 충족하면 True."""
    t = title.lower()
    # 1) 타이틀에 남성 키워드
    if any(kw in t for kw in MALE_MUST_KW):
        return True
    # 2) 네이버 카테고리 경로에 남성
    for field in ("category1", "category2", "category3", "category4"):
        cat_val = item_raw.get(field, "")
        if "남성" in cat_val:
            return True
    return False


def collect_all_male_products() -> dict[str, list[dict]]:
    """전 카테고리 남성 전용 상품 대량 수집. 남성 확인 필수."""
    pool = {}
    total = 0

    for category, queries in MALE_QUERIES.items():
        seen_imgs = set()
        products = []

        for query in queries:
            items = search_naver(query, display=30)
            for item in items:
                img = item.get("image", "")
                if not img or img in seen_imgs:
                    continue
                title = clean_title(item.get("title", ""))
                # 여성 키워드 → 즉시 제외
                if any(kw in title.lower() for kw in FEMALE_KW):
                    continue
                # 남성 확인 필수 (타이틀 or 카테고리)
                if not _is_confirmed_male(title, item):
                    continue
                seen_imgs.add(img)
                products.append({
                    "product_id": item.get("productId", ""),
                    "title": title,
                    "category": category,
                    "image_url": img,
                    "price": int(item.get("lprice", 0)),
                    "brand": item.get("brand", item.get("mallName", "")),
                    "gender": "male",
                })
            time.sleep(0.12)

        pool[category] = products
        print(f"  {category:15s}: {len(products)}개")
        total += len(products)

    print(f"  총: {total}개")
    return pool


def main():
    print("=" * 60)
    print("남성 코디 이미지 전면 교체")
    print("=" * 60)

    # 백업
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(DATA_DIR / "outfits_scored.json", DATA_DIR / f"outfits_scored_backup_{ts}.json")

    # 1. 수집
    print("\n[1] 네이버 API 전 카테고리 남성 상품 수집")
    pool = collect_all_male_products()

    # 저장
    pool_path = DATA_DIR / "male_products_full.json"
    pool_path.write_text(json.dumps(pool, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  저장: {pool_path.name}")

    # workout 풀 male도 통합
    wp_path = DATA_DIR / "workout_products.json"
    if wp_path.exists():
        wp = json.loads(wp_path.read_text(encoding="utf-8"))
        for cat, items in wp.items():
            male_items = [it for it in items if it.get("gender") == "male"]
            if cat not in pool:
                pool[cat] = []
            existing_imgs = {p["image_url"] for p in pool[cat]}
            for it in male_items:
                if it["image_url"] not in existing_imgs:
                    pool[cat].append(it)
                    existing_imgs.add(it["image_url"])

    # 2. 라운드로빈 큐 구축 (카테고리별 셔플)
    print("\n[2] 라운드로빈 큐 구축")
    queues = {}
    for cat, items in pool.items():
        imgs = list({it["image_url"]: it for it in items}.values())  # 중복 제거
        random.shuffle(imgs)
        queues[cat] = imgs
        print(f"  {cat:15s}: {len(imgs)}개")

    # 유사 카테고리 fallback
    FALLBACK = {
        "정장바지": "슬랙스", "코트": "자켓", "카디건": "니트",
        "가디건": "니트", "패딩": "자켓", "크로스백": "사이드백",
        "사이드백": "크로스백",
    }

    # 3. 남성 코디 이미지 전면 교체
    print("\n[3] 남성 코디 이미지 교체")
    outfits = json.loads((DATA_DIR / "outfits_scored.json").read_text(encoding="utf-8"))

    replaced = 0
    no_pool = 0
    queue_idx = defaultdict(int)

    for o in outfits:
        if o.get("gender") != "male":
            continue

        # workout은 별도 스크립트에서 처리하므로 스킵
        tpos = [t.lower() for t in (o.get("designed_tpo") or [])]
        if "workout" in tpos:
            continue

        for it in o.get("items", []):
            cat = it.get("category", "")
            q = queues.get(cat) or queues.get(FALLBACK.get(cat, ""), [])

            if not q:
                no_pool += 1
                continue

            idx = queue_idx[cat] % len(q)
            chosen = q[idx]
            queue_idx[cat] = idx + 1

            it["image_url"] = chosen["image_url"]
            if chosen.get("title"):
                it["title"] = chosen["title"]
            if chosen.get("brand"):
                it["brand"] = chosen["brand"]
            if chosen.get("price"):
                it["price"] = chosen["price"]
            replaced += 1

    print(f"  교체: {replaced}개")
    print(f"  풀 없음: {no_pool}개")

    # 저장
    (DATA_DIR / "outfits_scored.json").write_text(
        json.dumps(outfits, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 4. 검증
    print(f"\n{'=' * 60}")
    print("검증")
    print(f"{'=' * 60}")

    # 새로 수집한 이미지 셋
    fresh_male = set()
    for cat, items in pool.items():
        for it in items:
            fresh_male.add(it["image_url"])

    male_outfits = [o for o in outfits if o.get("gender") == "male"]
    non_workout = [o for o in male_outfits
                   if not (o.get("designed_tpo") and "workout" in [t.lower() for t in o["designed_tpo"]])]

    total_items = 0
    fresh_count = 0
    no_img = 0
    for o in non_workout:
        for it in o.get("items", []):
            total_items += 1
            img = it.get("image_url", "").strip()
            if not img:
                no_img += 1
            elif img in fresh_male:
                fresh_count += 1

    print(f"남성 비-workout 코디: {len(non_workout)}개, 아이템: {total_items}개")
    print(f"신규 남성 이미지: {fresh_count}/{total_items} ({fresh_count/total_items*100:.1f}%)")
    print(f"이미지 없음: {no_img}개")

    # 다양성 체크
    from collections import Counter
    cat_imgs = defaultdict(Counter)
    for o in non_workout:
        for it in o.get("items", []):
            cat = it.get("category", "?")
            img = it.get("image_url", "")
            if img:
                cat_imgs[cat][img] += 1

    print(f"\n카테고리별 다양성:")
    for cat in sorted(cat_imgs.keys()):
        total = sum(cat_imgs[cat].values())
        unique = len(cat_imgs[cat])
        top1 = cat_imgs[cat].most_common(1)
        top1_pct = top1[0][1] / total * 100 if top1 else 0
        print(f"  {cat:15s}: {unique:4d} unique / {total:4d} total ({unique/total*100:.0f}%) | top1 {top1_pct:.0f}%")


if __name__ == "__main__":
    main()
