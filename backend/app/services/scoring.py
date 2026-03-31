"""
추천 엔진 스코어링 모듈 — 5축 스코어링 함수.
각 함수는 순수 함수로 구현 (DB 의존 없음).
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from functools import lru_cache
from typing import Optional

# ──────────────────────────────────────────────
# 톤 ID 목록 (12-tone 퍼스널컬러)
# ──────────────────────────────────────────────
TONE_IDS = [
    "spring_warm_light", "spring_warm_bright", "spring_warm_mute",
    "summer_cool_light", "summer_cool_soft", "summer_cool_mute",
    "autumn_warm_deep", "autumn_warm_mute", "autumn_warm_bright",
    "winter_cool_deep", "winter_cool_bright", "winter_cool_light",
]

# ──────────────────────────────────────────────
# 12×12 톤 호환성 매트릭스
# tone_compat[user_tone][item_tone] → 점수 (0~100)
# 기획서 섹션 5.4: 동일 100, 호환(같은 시즌) 80~95, 반대 시즌 40~60, 기본 40
# ──────────────────────────────────────────────

_SEASONS = {
    "spring": ["spring_warm_light", "spring_warm_bright", "spring_warm_mute"],
    "summer": ["summer_cool_light", "summer_cool_soft", "summer_cool_mute"],
    "autumn": ["autumn_warm_deep", "autumn_warm_mute", "autumn_warm_bright"],
    "winter": ["winter_cool_deep", "winter_cool_bright", "winter_cool_light"],
}

_TEMP = {t: ("warm" if "warm" in t else "cool") for t in TONE_IDS}

_DEPTH = {}
for t in TONE_IDS:
    parts = t.split("_")
    _DEPTH[t] = parts[2]  # light, bright, mute, soft, deep


def _get_season(tone_id: str) -> str:
    return tone_id.split("_")[0]


def _build_tone_compat() -> dict[str, dict[str, int]]:
    """12×12 톤 호환성 매트릭스 생성.

    규칙:
    - 동일 톤 → 100
    - 같은 시즌 → 85~95 (명도/채도 유사성에 따라)
    - 같은 온도(웜/쿨), 다른 시즌 → 60~75
    - 반대 온도 → 40~55 (명도/채도 유사하면 약간 높음)
    """
    # 세부 유사도를 위한 depth 그룹
    depth_similarity = {
        ("light", "light"): 1.0,
        ("light", "bright"): 0.7,
        ("light", "mute"): 0.5,
        ("light", "soft"): 0.8,
        ("light", "deep"): 0.2,
        ("bright", "bright"): 1.0,
        ("bright", "mute"): 0.3,
        ("bright", "soft"): 0.4,
        ("bright", "deep"): 0.5,
        ("mute", "mute"): 1.0,
        ("mute", "soft"): 0.8,
        ("mute", "deep"): 0.4,
        ("soft", "soft"): 1.0,
        ("soft", "deep"): 0.3,
        ("deep", "deep"): 1.0,
    }
    # 양방향
    full_depth_sim = {}
    for (a, b), v in depth_similarity.items():
        full_depth_sim[(a, b)] = v
        full_depth_sim[(b, a)] = v

    compat: dict[str, dict[str, int]] = {}
    for u in TONE_IDS:
        compat[u] = {}
        u_season = _get_season(u)
        u_temp = _TEMP[u]
        u_depth = _DEPTH[u]

        for i in TONE_IDS:
            if u == i:
                compat[u][i] = 100
                continue

            i_season = _get_season(i)
            i_temp = _TEMP[i]
            i_depth = _DEPTH[i]

            ds = full_depth_sim.get((u_depth, i_depth), 0.5)

            if u_season == i_season:
                # 같은 시즌: 85 + depth_sim * 10 → 85~95
                compat[u][i] = round(85 + ds * 10)
            elif u_temp == i_temp:
                # 같은 온도, 다른 시즌 (봄↔가을 or 여름↔겨울)
                # 60 + depth_sim * 15 → 60~75
                compat[u][i] = round(60 + ds * 15)
            else:
                # 반대 온도 (웜↔쿨)
                # 40 + depth_sim * 15 → 40~55
                compat[u][i] = round(40 + ds * 15)

    return compat


TONE_COMPAT: dict[str, dict[str, int]] = _build_tone_compat()


# ──────────────────────────────────────────────
# 팔레트 로딩
# ──────────────────────────────────────────────
_PALETTE_DIR = Path(__file__).resolve().parents[2] / "data" / "palettes"


@lru_cache(maxsize=12)
def _load_palette(tone_id: str) -> list[tuple[int, int, int]]:
    """톤의 대표 팔레트 RGB 리스트를 로드한다."""
    path = _PALETTE_DIR / f"{tone_id}.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [tuple(c["rgb"]) for c in data["colors"]]


# ──────────────────────────────────────────────
# HEX → RGB 변환
# ──────────────────────────────────────────────
def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """HEX 색상 코드를 RGB 튜플로 변환한다."""
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# ──────────────────────────────────────────────
# RGB 유클리드 거리
# ──────────────────────────────────────────────
def _rgb_distance(c1: tuple[int, int, int], c2: tuple[int, int, int]) -> float:
    """두 RGB 색상 간 유클리드 거리를 계산한다."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


# 최대 RGB 거리: sqrt(255^2 * 3) = 441.67
_MAX_RGB_DISTANCE = math.sqrt(255**2 * 3)


# ──────────────────────────────────────────────
# PCF 스코어링 (퍼스널컬러 적합도)
# 기획서 섹션 5.5.1
# ──────────────────────────────────────────────
def calculate_pcf(
    item_tone_ids: list[Optional[str]],
    item_hex_colors: list[str],
    user_tone_id: str,
) -> float:
    """코디의 PCF(Personal Color Fit) 점수를 계산한다.

    Args:
        item_tone_ids: 코디 아이템들의 톤 ID 리스트 (None 가능)
        item_hex_colors: 코디 아이템들의 대표 HEX 색상 리스트
        user_tone_id: 사용자의 퍼스널컬러 톤 ID

    Returns:
        0~100 사이의 PCF 점수 (연속값)

    계산 로직 (기획서 5.5.1):
        1단계 - 톤 레벨 매칭: 톤 호환성 매트릭스에서 점수 조회
        2단계 - 색상 레벨 매칭: 톤 매칭 불가 시 RGB 거리 기반 점수
        3단계 - 모든 아이템 평균 → 코디 PCF
    """
    if not item_hex_colors:
        return 0.0

    user_palette = _load_palette(user_tone_id)
    item_scores: list[float] = []

    for tone_id, hex_color in zip(item_tone_ids, item_hex_colors):
        # 1단계: 톤 레벨 매칭
        if tone_id and tone_id in TONE_COMPAT.get(user_tone_id, {}):
            score = TONE_COMPAT[user_tone_id][tone_id]
            if score >= 85:  # 동일 톤(100) 또는 같은 시즌 호환(85~95)
                item_scores.append(float(score))
                continue

        # 2단계: 색상 레벨 매칭 (RGB 거리)
        item_rgb = _hex_to_rgb(hex_color)
        d_min = min(_rgb_distance(item_rgb, p) for p in user_palette)
        color_score = max(0.0, 100.0 - (d_min / (_MAX_RGB_DISTANCE / 100)))

        # 톤 매칭 점수와 색상 점수 중 높은 값 사용
        if tone_id and tone_id in TONE_COMPAT.get(user_tone_id, {}):
            tone_score = float(TONE_COMPAT[user_tone_id][tone_id])
            item_scores.append(max(tone_score, color_score))
        else:
            item_scores.append(color_score)

    # 3단계: 코디 전체 PCF = 아이템 평균
    return round(sum(item_scores) / len(item_scores), 2)
