"""
Step 5 취향 분석용 코디 이미지 자동 수집.

네이버 쇼핑 API에서 스타일 키워드별 대표 이미지 1장씩 다운로드.
4라운드 × 4장 = 16장.

사용법:
    cd backend
    python -m scripts.fetch_style_images
"""

import os
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")
SEARCH_URL = "https://openapi.naver.com/v1/search/shop.json"

OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "public" / "images" / "style"

# 4라운드 × 4키워드 — 각각 다른 스타일 분위기
ROUNDS = [
    ["여성 미니멀 코디", "여성 캐주얼 데일리룩", "여성 스트릿 코디", "여성 페미닌 블라우스 코디"],
    ["여성 모던 오피스룩", "여성 빈티지 원피스", "여성 스포티 코디", "여성 클래식 자켓 코디"],
    ["여성 오버사이즈 코디", "여성 슬림핏 니트", "여성 A라인 스커트 코디", "여성 레이어드 코디"],
    ["여성 베이지 뉴트럴 코디", "여성 비비드 컬러 코디", "여성 파스텔 봄 코디", "여성 모노톤 블랙 코디"],
]


def search_image(query: str) -> str | None:
    """네이버 쇼핑 API에서 첫 번째 상품 이미지 URL 반환."""
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {"query": query, "display": 5, "start": 1, "sort": "sim"}

    try:
        resp = requests.get(SEARCH_URL, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            items = resp.json().get("items", [])
            for item in items:
                img = item.get("image", "")
                if img and "pstatic.net" in img:
                    return img
        elif resp.status_code == 429:
            print(f"  Rate limit. 2초 대기...")
            time.sleep(2)
            return search_image(query)
    except Exception as e:
        print(f"  에러: {e}")
    return None


def download_image(url: str, path: Path) -> bool:
    """이미지 다운로드."""
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            path.write_bytes(resp.content)
            return True
    except Exception as e:
        print(f"  다운로드 실패: {e}")
    return False


def main():
    if not NAVER_CLIENT_ID:
        print("NAVER_CLIENT_ID 환경변수 없음. .env 확인.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    count = 0
    for round_idx, keywords in enumerate(ROUNDS):
        for img_idx, keyword in enumerate(keywords):
            num = round_idx * 4 + img_idx + 1
            filename = f"style_{num}.jpg"
            filepath = OUTPUT_DIR / filename

            print(f"[{num}/16] '{keyword}' 검색 중...")
            url = search_image(keyword)

            if url:
                if download_image(url, filepath):
                    print(f"  저장: {filename} ({len(filepath.read_bytes())} bytes)")
                    count += 1
                else:
                    print(f"  다운로드 실패")
            else:
                print(f"  이미지 못 찾음")

            time.sleep(0.3)  # rate limit 방지

    print(f"\n완료: {count}/16장 저장됨 → {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
