"""5축 스코어링 v2 — TPO·핏·컬러·스타일·리스크.

기존 OF/SF/PCF/CH 로직을 재구성하여 5개 독립 축으로 분리.
PE(가성비)는 Hard Filter H2에서 이미 처리되므로 bonus_pe로만 반영.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

_DATA = Path(__file__).resolve().parents[2] / "data"

# ── 데이터 로드 ──

def _load_json(name: str) -> dict:
    p = _DATA / name
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}

_TPO_FORMALITY = _load_json("tpo_formality_map.json")
_BODY_RULES = _load_json("body_type_rules.json")
_PROPORTION = _load_json("proportion_rules.json")
_STYLE_COMPAT = _load_json("style_tag_compat.json")

# 톤 호환 (기존 TONE_COMPAT 재사용)
_TONE_COMPAT: dict[str, dict[str, int]] | None = None

def _get_tone_compat() -> dict:
    global _TONE_COMPAT
    if _TONE_COMPAT is None:
        p = _DATA / "tone_compat.json"
        _TONE_COMPAT = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    return _TONE_COMPAT

# ── 가중치 ──

SCORING_WEIGHTS = {
    "tpo": 0.30,
    "fit": 0.15,
    "color": 0.20,
    "style": 0.20,
}
# risk는 가중합에 포함하지 않음 — 별도 감점


# ══════════════════════════════════════
# 4.1 TPO 적합도
# ══════════════════════════════════════

# 기존 OF 4-level matching
_TPO_SYNONYMS = {
    "commute": {"office", "meeting"},
    "interview": {"meeting"},
    "date": {"party"},
    "campus": {"daily", "casual"},
    "weekend": {"daily", "casual"},
    "travel": {"outdoor", "casual"},
    "event": {"party", "meeting"},
    "workout": {"outdoor"},
}
_TPO_GROUPS = {
    "formal": {"commute", "interview", "event", "meeting", "office"},
    "casual": {"campus", "weekend", "travel", "daily", "casual"},
    "active": {"workout", "outdoor"},
}


def _of_base(outfit_tpos: list[str], user_tpo_list: list[str]) -> float:
    """기존 OF 4-level."""
    outfit_set = {t.lower() for t in outfit_tpos}
    for ut in user_tpo_list:
        ut = ut.lower()
        if ut in outfit_set:
            return 100.0
        syns = _TPO_SYNONYMS.get(ut, set())
        if outfit_set & syns:
            return 85.0
    # group match
    for ut in user_tpo_list:
        ut = ut.lower()
        for grp, members in _TPO_GROUPS.items():
            if ut in members and outfit_set & members:
                return 65.0
    return 30.0


def calc_tpo(outfit: dict, user_tpo_list: list[str]) -> float:
    """TPO 적합도 (0-100). Formality 방향성 감점 포함."""
    outfit_tpos = outfit.get("designed_tpo") or []
    base = _of_base(outfit_tpos, user_tpo_list)

    # formality direction penalty
    items = outfit.get("items") or []
    formalities = [it.get("formality", 3.0) for it in items if it.get("formality")]
    if not formalities:
        return base

    avg_form = sum(formalities) / len(formalities)
    # 사용자 TPO의 기대 격식도
    expected = 3.0
    for ut in user_tpo_list:
        exp = _TPO_FORMALITY.get(ut.lower())
        if exp is not None:
            expected = exp
            break

    gap = abs(avg_form - expected)
    penalty = min(gap * 15, 30)
    return max(0.0, base - penalty)


# ══════════════════════════════════════
# 4.2 체형/핏 적합도
# ══════════════════════════════════════

def _sil_balance(items: list[dict]) -> float:
    """상하의 silhouette 호환성."""
    tops = [it.get("silhouette", "regular") for it in items
            if it.get("category", "") in {"셔츠", "블라우스", "니트", "맨투맨", "후드", "티셔츠", "반팔티", "크롭탑", "자켓", "코트", "바람막이", "패딩", "가디건"}]
    bots = [it.get("silhouette", "regular") for it in items
            if it.get("category", "") in {"슬랙스", "청바지", "반바지", "조거팬츠", "트레이닝팬츠", "스커트", "레깅스", "정장바지"}]
    if not tops or not bots:
        return 70.0  # 판단 불가 → 중립
    top_sil = tops[0]
    bot_sil = bots[0]
    return float(_PROPORTION.get(top_sil, {}).get(bot_sil, 70))


def _body_bonus(items: list[dict], body_type: str) -> float:
    """체형 규칙 기반 보너스."""
    rules = _BODY_RULES.get(body_type, _BODY_RULES.get("average", {}))
    rec = set(rules.get("recommended", []))
    avoid = set(rules.get("avoid", []))
    if not rec and not avoid:
        return 0.0

    sils = {it.get("silhouette", "regular") for it in items}
    if sils & avoid:
        return -20.0
    if sils & rec:
        return 15.0
    return 0.0


def calc_fit(outfit: dict, body_type: str | None = None) -> float:
    """체형/핏 적합도 (0-100). body_type이 None/빈값이면 'average' fallback."""
    bt = body_type if body_type else "average"
    items = outfit.get("items") or []
    sil = _sil_balance(items)
    body = _body_bonus(items, bt)
    body_component = max(0, min(100, 50 + body))
    return sil * 0.60 + body_component * 0.40


# ══════════════════════════════════════
# 4.3 컬러 조합
# ══════════════════════════════════════

def _tone_match(items: list[dict], user_tone_id: str) -> float:
    """기존 PCF: 아이템 톤과 사용자 톤 매칭."""
    if not user_tone_id:
        return 70.0
    scores = []
    compat = _get_tone_compat()
    for it in items:
        item_tone = it.get("tone_id", "")
        if item_tone == user_tone_id:
            scores.append(100.0)
        elif item_tone and user_tone_id:
            # 같은 시즌이면 85
            if item_tone.split("_")[0] == user_tone_id.split("_")[0]:
                scores.append(85.0)
            else:
                c = compat.get(user_tone_id, {}).get(item_tone, 60)
                scores.append(float(c))
        else:
            scores.append(70.0)
    return sum(scores) / len(scores) if scores else 70.0


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    if len(h) < 6:
        return (128, 128, 128)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _contrast_balance(items: list[dict]) -> float:
    """기존 CH: 아이템 간 색상 조화."""
    hexes = [it.get("color_hex", "") for it in items if it.get("color_hex") and len(it["color_hex"]) >= 7]
    if len(hexes) < 2:
        return 70.0
    rgbs = [_hex_to_rgb(h) for h in hexes]
    dists = []
    for i in range(len(rgbs)):
        for j in range(i + 1, len(rgbs)):
            d = math.sqrt(sum((a - b) ** 2 for a, b in zip(rgbs[i], rgbs[j])))
            dists.append(d)
    d_avg = sum(dists) / len(dists) if dists else 0
    if d_avg < 30:
        return 60.0
    elif d_avg < 80:
        return 80.0 + (d_avg - 30) / 50 * 20
    elif d_avg < 150:
        return 100.0 - (d_avg - 80) / 70 * 21
    else:
        return max(30.0, 79.0 - (d_avg - 150) / 290 * 49)


def _tone_consistency(items: list[dict]) -> float:
    """아이템 간 tone_id 일관성."""
    tones = {it.get("tone_id", "") for it in items if it.get("tone_id")}
    if len(tones) <= 2:
        return 100.0
    return max(50.0, 100.0 - (len(tones) - 2) * 15)


def calc_color(outfit: dict, user_tone_id: str) -> float:
    """컬러 조합 (0-100)."""
    items = outfit.get("items") or []
    tone = _tone_match(items, user_tone_id)
    contrast = _contrast_balance(items)
    consistency = _tone_consistency(items)
    return tone * 0.45 + contrast * 0.35 + consistency * 0.20


# ══════════════════════════════════════
# 4.4 스타일 일관성
# ══════════════════════════════════════

def _category_compat(items: list[dict]) -> float:
    """기존 style_compat.json 기반 카테고리 궁합."""
    # 간이 구현: style_tag 기반
    tags = [it.get("style_tag", "") for it in items if it.get("style_tag")]
    if len(tags) <= 1:
        return 85.0
    # 쌍별 점수 평균
    scores = []
    for i in range(len(tags)):
        for j in range(i + 1, len(tags)):
            pair = "+".join(sorted([tags[i], tags[j]]))
            s = _STYLE_COMPAT.get(pair, 60)
            scores.append(float(s))
    return sum(scores) / len(scores) if scores else 70.0


def _style_coherence(items: list[dict]) -> float:
    """style_tag 통일성."""
    tags = [it.get("style_tag", "") for it in items if it.get("style_tag")]
    unique = set(tags)
    if len(unique) <= 1:
        return 100.0
    if len(unique) == 2:
        pair = "+".join(sorted(unique))
        return float(_STYLE_COMPAT.get(pair, 60))
    return max(20.0, 100.0 - (len(unique) - 1) * 25)


def _mood_consistency(outfit: dict) -> float:
    """designed_moods 일관성."""
    moods = outfit.get("designed_moods") or []
    unique = set(moods)
    if len(unique) <= 2:
        return 100.0
    return max(40.0, 100.0 - (len(unique) - 2) * 20)


def calc_style(outfit: dict) -> float:
    """스타일 일관성 (0-100)."""
    items = outfit.get("items") or []
    cat = _category_compat(items)
    coh = _style_coherence(items)
    mood = _mood_consistency(outfit)
    return cat * 0.45 + coh * 0.35 + mood * 0.20


# ══════════════════════════════════════
# 4.5 리스크 관리
# ══════════════════════════════════════

def _count_high_saturation(items: list[dict]) -> int:
    """고채도 색상 수."""
    count = 0
    for it in items:
        h = it.get("color_hex", "")
        if not h or len(h) < 7:
            continue
        r, g, b = _hex_to_rgb(h)
        mx, mn = max(r, g, b), min(r, g, b)
        sat = (mx - mn) / max(mx, 1)
        if sat > 0.7:
            count += 1
    return count


def _is_volume_clash(items: list[dict]) -> bool:
    """상하의 모두 oversized/wide인 극단 케이스."""
    top_cats = {"셔츠", "블라우스", "니트", "맨투맨", "후드", "티셔츠", "자켓", "코트"}
    bot_cats = {"슬랙스", "청바지", "반바지", "조거팬츠", "스커트"}
    top_sils = [it.get("silhouette", "") for it in items if it.get("category", "") in top_cats]
    bot_sils = [it.get("silhouette", "") for it in items if it.get("category", "") in bot_cats]
    big = {"oversized", "wide", "relaxed"}
    return bool(top_sils and bot_sils
                and any(s in big for s in top_sils)
                and any(s in big for s in bot_sils))


def calc_risk(outfit: dict, tpo_score: float, fit_score: float,
              color_score: float, style_score: float) -> float:
    """리스크 감점 (-30 ~ 0).

    중복 감점 방지 원칙:
    - formality 방향성 → TPO축에서만 처리 (여기서 금지)
    - formality std(편차) → TPO축에서만 처리 (여기서 금지)
    - style_tag 불일치 → STYLE축에서만 처리 (여기서 금지)
    - 이 축은 오직 "복합 위험"만 감지 (개별 축에서 못 잡는 것)
    """
    items = outfit.get("items") or []
    penalty = 0.0

    # Rule 1: 과한 트렌드 아이템
    trend_count = sum(1 for it in items
                      if any(t in (it.get("tags") or []) for t in ("trend", "bold")))
    if trend_count >= 3:
        penalty -= 12
    elif trend_count == 2:
        penalty -= 5

    # Rule 2: 컬러 과부하
    sat_count = _count_high_saturation(items)
    if sat_count >= 4:
        penalty -= 10
    elif sat_count >= 3:
        penalty -= 5

    # Rule 3: 실루엣 충돌
    if _is_volume_clash(items):
        penalty -= 10

    # Rule 4: 복합 위험 (2개 이상 축이 동시에 낮을 때)
    low_axes = sum(1 for s in [tpo_score, fit_score, color_score, style_score] if s < 50)
    if low_axes >= 3:
        penalty -= 15
    elif low_axes >= 2:
        penalty -= 8

    return max(penalty, -30.0)


# ══════════════════════════════════════
# FINAL
# ══════════════════════════════════════

def compute_scores_v2(
    outfit: dict,
    user_tone_id: str = "",
    user_tpo_list: list[str] | None = None,
    body_type: str | None = None,
    height_range: str | None = None,
) -> dict[str, float]:
    """5축 스코어 계산 → {tpo, fit, color, style, risk, final}.

    body_type/height_range가 None이면 'average' fallback.
    """
    if user_tpo_list is None:
        user_tpo_list = []

    tpo = calc_tpo(outfit, user_tpo_list)
    fit = calc_fit(outfit, body_type or "average")
    color = calc_color(outfit, user_tone_id)
    style = calc_style(outfit)
    risk = calc_risk(outfit, tpo, fit, color, style)

    weighted = (
        tpo * SCORING_WEIGHTS["tpo"]
        + fit * SCORING_WEIGHTS["fit"]
        + color * SCORING_WEIGHTS["color"]
        + style * SCORING_WEIGHTS["style"]
    )
    # 정규화: 0.85 스케일 → 0-100
    normalized = weighted / 0.85
    final = max(0.0, min(100.0, normalized + risk))

    return {
        "tpo": round(tpo, 2),
        "fit": round(fit, 2),
        "color": round(color, 2),
        "style": round(style, 2),
        "risk": round(risk, 2),
        "final": round(final, 2),
    }
