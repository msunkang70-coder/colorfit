"""
TPO별 코디 키워드로 네이버 쇼핑 API에서 상품 수집.
기존 단품 키워드("코랄 블라우스") 대신 코디/룩 키워드("여성 출근룩 코디")로 수집.

수집된 상품을 outfits_scored.json에 새 코디로 추가.

사용법:
    cd backend
    python -m scripts.fetch_coordi_products
"""

import json
import os
import time
import hashlib
from pathlib import Path
from collections import Counter
from dotenv import load_dotenv

import requests

load_dotenv()

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")
SEARCH_URL = "https://openapi.naver.com/v1/search/shop.json"

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SCORED_PATH = DATA_DIR / "outfits_scored.json"

# TPO × 성별 코디 키워드 (핵심)
COORDI_QUERIES = {
    "commute": {
        "female": [
            "여성 출근룩 코디", "여성 오피스룩 셔츠 슬랙스", "여성 출근 자켓 정장",
            "여성 오피스 블라우스 스커트", "여성 비즈니스 캐주얼 세트",
            "여성 출근 니트 슬랙스", "여성 오피스 자켓 원피스",
        ],
        "male": [
            "남성 출근룩 코디", "남성 오피스룩 셔츠 슬랙스", "남성 비즈니스 캐주얼",
            "남성 출근 자켓 치노", "남성 오피스 니트 슬랙스",
        ],
    },
    "interview": {
        "female": [
            "여성 면접룩 정장", "여성 면접 자켓 슬랙스 세트", "여성 면접 블라우스 정장",
            "여성 포멀 자켓 스커트", "여성 면접 정장 세트",
        ],
        "male": [
            "남성 면접 정장 세트", "남성 면접룩 자켓 슬랙스", "남성 면접 셔츠 정장",
        ],
    },
    "date": {
        "female": [
            "여성 데이트룩 코디", "여성 소개팅 코디", "여성 데이트 원피스",
            "여성 데이트 블라우스 스커트", "여성 봄 데이트 코디",
        ],
        "male": [
            "남성 데이트룩 코디", "남성 소개팅 코디", "남성 데이트 셔츠 슬랙스",
        ],
    },
    "campus": {
        "female": [
            "여성 캠퍼스룩 코디", "여성 대학생 코디", "여성 캐주얼 데일리룩",
        ],
        "male": [
            "남성 캠퍼스룩 코디", "남성 대학생 코디", "남성 캐주얼 데일리룩",
        ],
    },
    "weekend": {
        "female": [
            "여성 주말 나들이 코디", "여성 캐주얼 주말룩", "여성 봄 나들이 코디",
        ],
        "male": [
            "남성 주말 코디", "남성 캐주얼 주말룩",
        ],
    },
    "workout": {
        "female": [
            "여성 운동복 레깅스 세트", "여성 애슬레저 코디", "여성 짐웨어 세트",
        ],
        "male": [
            "남성 운동복 세트", "남성 짐웨어 코디",
        ],
    },
}

# 카테고리 추정 키워드
CAT_KEYWORDS = {
    "자켓": ["자켓", "재킷", "블레이저"],
    "셔츠": ["셔츠", "남방"],
    "블라우스": ["블라우스"],
    "니트": ["니트", "스웨터"],
    "슬랙스": ["슬랙스", "정장바지"],
    "스커트": ["스커트", "치마"],
    "원피스": ["원피스", "드레스"],
    "티셔츠": ["티셔츠", "반팔"],
    "코트": ["코트", "트렌치"],
}


def search_products(query, display=20):
    """네이버 쇼핑 API 검색."""
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {"query": query, "display": display, "start": 1, "sort": "sim"}

    try:
        resp = requests.get(SEARCH_URL, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("items", [])
        if resp.status_code == 429:
            time.sleep(2)
            return search_products(query, display)
    except Exception as e:
        print(f"  API 에러: {e}")
    return []


def guess_category(title):
    """상품명에서 카테고리 추정."""
    title_lower = title.lower()
    for cat, keywords in CAT_KEYWORDS.items():
        for kw in keywords:
            if kw in title_lower:
                return cat
    return "기타"


def make_outfit_id(tpo, gender, idx):
    """고유 outfit_id 생성."""
    h = hashlib.md5(f"{tpo}_{gender}_{idx}_{time.time()}".encode()).hexdigest()[:8]
    return f"coordi_{tpo}_{gender}_{h}"


def main():
    if not NAVER_CLIENT_ID:
        print("NAVER_CLIENT_ID 없음")
        return

    with open(SCORED_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    before_count = len(data)
    existing_ids = {o.get("outfit_id") for o in data}
    new_outfits = []
    stats = Counter()

    for tpo, genders in COORDI_QUERIES.items():
        for gender, queries in genders.items():
            for query in queries:
                print(f"[{tpo}/{gender}] '{query}'")
                items = search_products(query, display=10)

                for item in items:
                    title = item.get("title", "").replace("<b>", "").replace("</b>", "")
                    image = item.get("image", "")
                    price = int(item.get("lprice", 0))
                    pid = item.get("productId", "")
                    mall = item.get("mallName", "")

                    if not image or price < 5000 or price > 500000:
                        continue

                    cat = guess_category(title)
                    if cat == "기타":
                        continue

                    # 단품을 코디 아이템으로 구성
                    outfit_item = {
                        "product_id": str(pid),
                        "name": title,
                        "category": cat,
                        "brand": mall,
                        "price": price,
                        "image_url": image,
                        "mall_name": mall,
                        "mall_url": item.get("link", ""),
                        "color_hex": "#808080",
                        "tone_id": "",
                        "gender": gender,
                        "formality": 4 if tpo in ("interview", "commute", "event") else 3 if tpo == "date" else 2,
                        "silhouette": "regular",
                    }

                    oid = make_outfit_id(tpo, gender, pid)
                    if oid in existing_ids:
                        continue

                    outfit = {
                        "outfit_id": oid,
                        "items": [outfit_item],
                        "designed_tpo": [tpo],
                        "tags": [tpo],
                        "total_price": price,
                        "is_complete_outfit": False,
                        "gender": gender,
                    }

                    new_outfits.append(outfit)
                    existing_ids.add(oid)
                    stats[f"{tpo}_{gender}"] += 1

                time.sleep(0.5)

    # 기존 데이터에 추가
    data.extend(new_outfits)

    with open(SCORED_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    print(f"\n=== 결과 ===")
    print(f"기존 코디: {before_count}")
    print(f"추가 코디: {len(new_outfits)}")
    print(f"최종 코디: {len(data)}")
    print(f"\nTPO별 추가:")
    for k, v in stats.most_common():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
