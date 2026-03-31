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
    if len(h) < 6:
        return (128, 128, 128)  # fallback: 중간 회색
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
    if not item_hex_colors or not user_tone_id:
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


# ──────────────────────────────────────────────
# OF 스코어링 (TPO 적합도)
# 기획서 섹션 5.5.2
# ──────────────────────────────────────────────

# TPO 동의어 확장 매핑
# 기획서: commute↔office, weekend↔casual↔daily, interview→office(단방향 확장 아님, interview쪽에서만)
TPO_SYNONYMS: dict[str, set[str]] = {
    "commute": {"office", "commute"},
    "office": {"office", "commute"},
    "weekend": {"casual", "weekend", "daily"},
    "casual": {"casual", "weekend", "daily"},
    "daily": {"casual", "daily", "weekend"},
    "interview": {"interview", "office"},
    "campus": {"campus", "casual"},
    "event": {"party", "wedding", "event"},
    "party": {"party", "event"},
    "wedding": {"wedding", "event"},
    "workout": {"workout"},
}


def calculate_of(
    outfit_tags: list[str],
    user_tpo_list: list[str],
) -> float:
    """코디의 OF(Occasion Fit) 점수를 계산한다.

    Args:
        outfit_tags: 코디에 부여된 TPO 태그 리스트
        user_tpo_list: 사용자가 설정한 TPO 리스트

    Returns:
        30~100 사이의 OF 점수 (30점 하한)

    계산 로직 (기획서 5.5.2):
        1. 사용자 TPO를 동의어 확장 → expanded_tpos 집합
        2. outfit_tags와 교집합 크기(match_count) 산출
        3. match_count 기반 점수 변환
    """
    if not outfit_tags or not user_tpo_list:
        return 30.0

    # 1. 사용자 TPO 동의어 확장
    expanded_tpos: set[str] = set()
    for tpo in user_tpo_list:
        tpo_lower = tpo.lower()
        expanded_tpos.update(TPO_SYNONYMS.get(tpo_lower, {tpo_lower}))

    # 2. 매칭 수 산출
    outfit_tag_set = {t.lower() for t in outfit_tags}
    match_count = len(outfit_tag_set & expanded_tpos)
    total_tags = len(outfit_tag_set)

    if total_tags == 0:
        return 30.0

    # 3. 점수 변환
    if match_count >= 2:
        score = 80.0 + (match_count / total_tags) * 20.0
    elif match_count == 1:
        score = 60.0 + (1.0 / total_tags) * 20.0
    else:
        score = 30.0

    return round(min(score, 100.0), 2)


# ──────────────────────────────────────────────
# CH 스코어링 (색상 조화도)
# 기획서 섹션 5.5.3
# ──────────────────────────────────────────────

def _rgb_to_hsv(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    """RGB → HSV 변환. S, V는 0~1 범위."""
    r, g, b = rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0
    mx = max(r, g, b)
    mn = min(r, g, b)
    diff = mx - mn

    # Hue
    if diff == 0:
        h = 0.0
    elif mx == r:
        h = (60 * ((g - b) / diff) + 360) % 360
    elif mx == g:
        h = (60 * ((b - r) / diff) + 120) % 360
    else:
        h = (60 * ((r - g) / diff) + 240) % 360

    # Saturation
    s = 0.0 if mx == 0 else diff / mx

    return (h, s, mx)


def calculate_ch(item_hex_colors: list[str]) -> float:
    """코디의 CH(Color Harmony) 점수를 계산한다.

    Args:
        item_hex_colors: 코디 아이템들의 HEX 색상 리스트

    Returns:
        0~100 사이의 CH 점수

    계산 로직 (기획서 5.5.3):
        1. 모든 아이템 쌍의 RGB 유클리드 거리 → 평균 d_avg
        2. d_avg 구간별 점수 변환
        3. 채도 보너스 (+5점, 아이템≥3 & 채도 표준편차 0.15~0.40)
    """
    if len(item_hex_colors) < 2:
        return 70.0  # 단일 아이템은 중립 점수

    rgbs = [_hex_to_rgb(c) for c in item_hex_colors]

    # 1. 모든 쌍의 RGB 거리 → 평균
    distances: list[float] = []
    for i in range(len(rgbs)):
        for j in range(i + 1, len(rgbs)):
            distances.append(_rgb_distance(rgbs[i], rgbs[j]))

    d_avg = sum(distances) / len(distances)

    # 2. 구간별 점수
    if d_avg < 30:
        score = 60.0
    elif d_avg < 80:
        score = 80.0 + (d_avg - 30) / 50 * 20
    elif d_avg < 150:
        score = 100.0 - (d_avg - 80) / 70 * 21
    else:
        score = max(30.0, 79.0 - (d_avg - 150) / 290 * 49)

    # 3. 채도 보너스
    if len(item_hex_colors) >= 3:
        saturations = [_rgb_to_hsv(rgb)[1] for rgb in rgbs]
        mean_s = sum(saturations) / len(saturations)
        std_s = math.sqrt(sum((s - mean_s) ** 2 for s in saturations) / len(saturations))
        if 0.15 <= std_s <= 0.40:
            score += 5.0

    return round(min(max(score, 0.0), 100.0), 2)


# ──────────────────────────────────────────────
# PE 스코어링 (가격 효율성)
# 기획서 섹션 5.5.4
# ──────────────────────────────────────────────

def calculate_pe(
    total_price: int | float,
    budget_min: int | float,
    budget_max: int | float,
) -> float:
    """코디의 PE(Price Efficiency) 점수를 계산한다.

    Args:
        total_price: 코디 총 가격
        budget_min: 사용자 최소 예산
        budget_max: 사용자 최대 예산

    Returns:
        0~100 사이의 PE 점수

    계산 로직 (기획서 5.5.4):
        Case 1: 예산 범위 내 → 중앙 가까울수록 높은 점수 (최대 100)
        Case 2: 예산 초과 → 감점 (70점 기반, 70% 초과 시 0점)
        Case 3: 예산 미만 → 완만 감점 (최저 40점)
    """
    if budget_max <= 0 or budget_min < 0:
        return 50.0

    budget_mid = (budget_min + budget_max) / 2

    if budget_min <= total_price <= budget_max:
        # Case 1: 예산 범위 내
        if budget_mid == 0:
            return 100.0
        score = 100.0 - abs(total_price - budget_mid) / budget_mid * 30
    elif total_price > budget_max:
        # Case 2: 예산 초과
        over_ratio = (total_price - budget_max) / budget_max
        score = max(0.0, 70.0 - over_ratio * 100)
    else:
        # Case 3: 예산 미만
        if budget_min == 0:
            return 80.0
        under_ratio = (budget_min - total_price) / budget_min
        score = max(40.0, 80.0 - under_ratio * 80)

    return round(min(max(score, 0.0), 100.0), 2)


# ──────────────────────────────────────────────
# SF 스코어링 (스타일 적합도)
# 기획서 섹션 5.5.5, 6.6
# ──────────────────────────────────────────────

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"


@lru_cache(maxsize=1)
def _load_style_compat() -> dict[str, int]:
    """카테고리 궁합 매트릭스 로드. 양방향 조회 지원 (키를 알파벳순 정규화)."""
    with open(_DATA_DIR / "style_compat.json", "r", encoding="utf-8") as f:
        raw = json.load(f)
    normalized: dict[str, int] = {}
    for k, v in raw.items():
        if k.startswith("_"):
            continue
        parts = k.split("|")
        if len(parts) == 2:
            key = "|".join(sorted(parts))
            normalized[key] = v
    return normalized


@lru_cache(maxsize=1)
def _load_silhouette_rules() -> dict[str, dict]:
    """실루엣 조합 규칙 로드."""
    with open(_DATA_DIR / "silhouette_rules.json", "r", encoding="utf-8") as f:
        raw = json.load(f)
    return {k: v for k, v in raw.items() if not k.startswith("_")}


@lru_cache(maxsize=1)
def _load_formality_map() -> dict[str, int]:
    """아이템별 포멀도 매핑 로드."""
    with open(_DATA_DIR / "formality_map.json", "r", encoding="utf-8") as f:
        raw = json.load(f)
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def _compat_key(cat1: str, cat2: str) -> str:
    """두 카테고리를 알파벳순으로 정렬하여 키 생성."""
    a, b = sorted([cat1.lower(), cat2.lower()])
    return f"{a}|{b}"


def _category_compat_score(categories: list[str]) -> float:
    """카테고리 궁합 점수 (0~100). 모든 쌍의 평균."""
    if len(categories) < 2:
        return 70.0

    compat = _load_style_compat()
    scores: list[float] = []

    for i in range(len(categories)):
        for j in range(i + 1, len(categories)):
            key = _compat_key(categories[i], categories[j])
            scores.append(float(compat.get(key, 60.0)))  # 미등록 조합 → 60점

    return sum(scores) / len(scores)


def _silhouette_score(top_silhouette: Optional[str], bottom_silhouette: Optional[str]) -> float:
    """실루엣 밸런스 점수 (0~100)."""
    if not top_silhouette or not bottom_silhouette:
        return 70.0  # 정보 없으면 중립

    rules = _load_silhouette_rules()
    key = f"{top_silhouette.lower()}|{bottom_silhouette.lower()}"
    rule = rules.get(key)
    if rule:
        return float(rule["score"])

    return 65.0  # 미등록 조합 → 중간 점수


def _formality_score(categories: list[str]) -> float:
    """포멀도 일관성 점수 (0~100). 표준편차 × 40 감점."""
    if len(categories) < 2:
        return 100.0

    fmap = _load_formality_map()
    formalities = [float(fmap.get(c.lower(), 3)) for c in categories]  # 미등록 → 3(중간)

    mean_f = sum(formalities) / len(formalities)
    std_f = math.sqrt(sum((f - mean_f) ** 2 for f in formalities) / len(formalities))

    return round(max(0.0, 100.0 - std_f * 40), 2)


def calculate_sf(
    categories: list[str],
    top_silhouette: Optional[str] = None,
    bottom_silhouette: Optional[str] = None,
) -> float:
    """코디의 SF(Style Fit) 점수를 계산한다.

    Args:
        categories: 코디 아이템들의 카테고리 리스트
        top_silhouette: 상의 실루엣 (oversized/fitted/crop/regular)
        bottom_silhouette: 하의 실루엣 (slim/skinny/wide/flared/straight/high_waist)

    Returns:
        0~100 사이의 SF 점수

    계산 로직 (기획서 5.5.5):
        SF = category_score × 0.50 + silhouette_score × 0.25 + formality_score × 0.25
    """
    if not categories:
        return 50.0

    cat_score = _category_compat_score(categories)
    sil_score = _silhouette_score(top_silhouette, bottom_silhouette)
    form_score = _formality_score(categories)

    sf = cat_score * 0.50 + sil_score * 0.25 + form_score * 0.25
    return round(min(max(sf, 0.0), 100.0), 2)
