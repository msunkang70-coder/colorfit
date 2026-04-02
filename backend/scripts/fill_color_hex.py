"""
color_hex 추출 스크립트 — 아이템 이미지에서 대표 색상을 추출하여 color_hex 필드를 채운다.

사용법:
    cd backend
    python -m scripts.fill_color_hex
"""

import json
import sys
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SCORED_PATH = DATA_DIR / "outfits_scored.json"

HEADERS = {
    "Referer": "https://search.shopping.naver.com/",
    "User-Agent": "Mozilla/5.0",
}


def extract_color(image_url: str) -> str | None:
    """이미지 URL에서 대표 색상 HEX를 추출."""
    try:
        resp = requests.get(image_url, headers=HEADERS, timeout=8)
        if resp.status_code != 200:
            return None
        img = Image.open(BytesIO(resp.content)).convert("RGB")
        img = img.resize((32, 32), Image.LANCZOS)
        # 중앙 16x16 영역
        crop = img.crop((8, 8, 24, 24))
        pixels = list(crop.getdata())
        r = sum(p[0] for p in pixels) // len(pixels)
        g = sum(p[1] for p in pixels) // len(pixels)
        b = sum(p[2] for p in pixels) // len(pixels)
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return None


def main():
    with open(SCORED_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    total = 0
    skipped = 0
    success = 0
    failed = 0

    items_to_process = []
    for o in data:
        for it in o.get("items", []):
            total += 1
            if it.get("color_hex") and it["color_hex"] != "" and it["color_hex"] != "#808080":
                skipped += 1
                continue
            url = it.get("image_url", "")
            if url:
                items_to_process.append(it)

    print(f"총 아이템: {total}")
    print(f"이미 color_hex 있음 (스킵): {skipped}")
    print(f"처리 대상: {len(items_to_process)}")

    batch_size = 50
    for i, it in enumerate(items_to_process):
        url = it.get("image_url", "")
        color = extract_color(url)
        if color:
            it["color_hex"] = color
            success += 1
        else:
            it["color_hex"] = "#808080"
            failed += 1

        if (i + 1) % batch_size == 0:
            print(f"  진행: {i+1}/{len(items_to_process)} (성공: {success}, 실패: {failed})")
            # 중간 저장
            with open(SCORED_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)

    # 최종 저장
    with open(SCORED_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    print(f"\n=== 결과 ===")
    print(f"성공: {success}")
    print(f"실패 (fallback #808080): {failed}")
    print(f"스킵: {skipped}")
    print(f"성공률: {success/(success+failed)*100:.1f}%" if (success + failed) > 0 else "N/A")


if __name__ == "__main__":
    main()
