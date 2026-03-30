"""
color_extractor.py — 이미지에서 dominant color 추출 + 12톤 매핑

기능:
    1. 이미지 URL에서 상위 3개 dominant color 추출 (K-means)
    2. 추출된 색상을 12톤 팔레트와 RGB 유클리드 거리 비교
    3. 가장 가까운 톤 ID 매핑
"""

import io
import json
import logging
import math
from pathlib import Path

import numpy as np
import requests
from PIL import Image
from sklearn.cluster import KMeans

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PALETTES_DIR = PROJECT_ROOT / "backend" / "data" / "palettes"

# ── 팔레트 로딩 ─────────────────────────────────────────────

_palette_cache: dict[str, list[list[int]]] | None = None


def load_palettes() -> dict[str, list[list[int]]]:
    """12톤 팔레트를 로드한다. {tone_id: [[r,g,b], ...]}"""
    global _palette_cache
    if _palette_cache is not None:
        return _palette_cache

    _palette_cache = {}
    for path in sorted(PALETTES_DIR.glob("*.json")):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        tone_id = data["tone_id"]
        colors = [c["rgb"] for c in data["colors"]]
        _palette_cache[tone_id] = colors

    return _palette_cache


# ── 색상 추출 ───────────────────────────────────────────────

def hex_to_rgb(hex_str: str) -> list[int]:
    """HEX 문자열을 RGB 리스트로 변환한다."""
    hex_str = hex_str.lstrip("#")
    return [int(hex_str[i:i+2], 16) for i in (0, 2, 4)]


def rgb_to_hex(rgb: list[int] | np.ndarray) -> str:
    """RGB를 HEX 문자열로 변환한다."""
    return "#{:02X}{:02X}{:02X}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))


def extract_dominant_colors(
    image: Image.Image,
    n_colors: int = 3,
    sample_size: int = 5000,
) -> list[dict]:
    """
    이미지에서 상위 n개 dominant color를 추출한다.

    Returns:
        [{"hex": "#FF6B6B", "rgb": [255,107,107], "ratio": 0.45}, ...]
    """
    img = image.convert("RGB")
    img = img.resize((150, 150))  # 성능을 위해 리사이즈

    pixels = np.array(img).reshape(-1, 3).astype(np.float64)

    # 배경색(흰색/검정) 비중이 높은 경우 필터링
    # 흰색(>240) 및 검정(<15) 근처 픽셀 제거
    mask = ~(
        ((pixels[:, 0] > 240) & (pixels[:, 1] > 240) & (pixels[:, 2] > 240)) |
        ((pixels[:, 0] < 15) & (pixels[:, 1] < 15) & (pixels[:, 2] < 15))
    )
    filtered = pixels[mask]

    if len(filtered) < 100:
        filtered = pixels  # 필터 후 너무 적으면 원본 사용

    # 샘플링
    if len(filtered) > sample_size:
        indices = np.random.choice(len(filtered), sample_size, replace=False)
        filtered = filtered[indices]

    n_colors = min(n_colors, len(filtered))
    kmeans = KMeans(n_clusters=n_colors, n_init=10, random_state=42)
    kmeans.fit(filtered)

    centers = kmeans.cluster_centers_
    labels = kmeans.labels_
    counts = np.bincount(labels)
    ratios = counts / counts.sum()

    # 비율 순으로 정렬
    order = np.argsort(-ratios)
    results = []
    for idx in order:
        rgb = centers[idx].astype(int).tolist()
        results.append({
            "hex": rgb_to_hex(rgb),
            "rgb": rgb,
            "ratio": round(float(ratios[idx]), 3),
        })

    return results


def extract_from_url(url: str, n_colors: int = 3, timeout: int = 10) -> list[dict]:
    """이미지 URL에서 dominant color를 추출한다."""
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content))
        return extract_dominant_colors(img, n_colors=n_colors)
    except Exception as e:
        logger.warning("이미지 색상 추출 실패: %s — %s", url, e)
        return []


# ── 12톤 매핑 ───────────────────────────────────────────────

def rgb_distance(c1: list[int], c2: list[int]) -> float:
    """두 RGB 색상 간 유클리드 거리."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


def map_color_to_tone(rgb: list[int]) -> tuple[str, float]:
    """
    단일 RGB 색상을 가장 가까운 톤에 매핑한다.

    Returns:
        (tone_id, min_distance)
    """
    palettes = load_palettes()
    best_tone = ""
    best_dist = float("inf")

    for tone_id, palette_colors in palettes.items():
        for pc in palette_colors:
            dist = rgb_distance(rgb, pc)
            if dist < best_dist:
                best_dist = dist
                best_tone = tone_id

    return best_tone, best_dist


def map_colors_to_tone(colors: list[dict]) -> tuple[str, list[str]]:
    """
    여러 dominant color를 종합하여 상품의 톤을 결정한다.

    가중 평균: 각 색상의 비율(ratio)을 가중치로 사용하여
    가장 적합한 톤을 선정한다.

    Returns:
        (best_tone_id, compatible_tone_ids)
    """
    if not colors:
        return "", []

    # 톤별 가중 거리 합산
    palettes = load_palettes()
    tone_scores: dict[str, float] = {t: 0.0 for t in palettes}

    for color in colors:
        rgb = color["rgb"]
        ratio = color.get("ratio", 1.0)

        for tone_id, palette_colors in palettes.items():
            min_dist = min(rgb_distance(rgb, pc) for pc in palette_colors)
            tone_scores[tone_id] += min_dist * ratio

    # 가장 거리가 짧은(점수 낮은) 톤이 best
    sorted_tones = sorted(tone_scores.items(), key=lambda x: x[1])
    best_tone = sorted_tones[0][0]

    # 호환 톤: best 대비 1.3배 이내 거리인 톤들
    best_score = sorted_tones[0][1]
    threshold = best_score * 1.3 if best_score > 0 else 50
    compatible = [t for t, s in sorted_tones[1:4] if s <= threshold]

    return best_tone, compatible
