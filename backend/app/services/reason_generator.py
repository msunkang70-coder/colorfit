"""
추천 이유 생성기 — 5축 가중 기여도 기반 자연어 이유 생성.
기획서 섹션 6.4 참조.
"""

from __future__ import annotations

from app.services.feed_builder import DEFAULT_WEIGHTS

# ──────────────────────────────────────────────
# 톤별 한글 이름 매핑
# ──────────────────────────────────────────────
TONE_NAMES_KO: dict[str, str] = {
    "spring_warm_light": "봄웜라이트",
    "spring_warm_bright": "봄웜브라이트",
    "spring_warm_mute": "봄웜뮤트",
    "summer_cool_light": "여름쿨라이트",
    "summer_cool_soft": "여름쿨소프트",
    "summer_cool_mute": "여름쿨뮤트",
    "autumn_warm_deep": "가을웜딥",
    "autumn_warm_mute": "가을웜뮤트",
    "autumn_warm_bright": "가을웜브라이트",
    "winter_cool_deep": "겨울쿨딥",
    "winter_cool_bright": "겨울쿨브라이트",
    "winter_cool_light": "겨울쿨라이트",
}

# ──────────────────────────────────────────────
# TPO 한글 매핑
# ──────────────────────────────────────────────
TPO_NAMES_KO: dict[str, str] = {
    "commute": "출근",
    "office": "오피스",
    "weekend": "주말",
    "casual": "캐주얼",
    "daily": "데일리",
    "interview": "면접",
    "campus": "캠퍼스",
    "event": "행사",
    "party": "파티",
    "wedding": "웨딩",
    "workout": "운동",
    "date": "데이트",
    "travel": "여행",
}

# ──────────────────────────────────────────────
# 템플릿 (기획서 6.4)
# ──────────────────────────────────────────────
TEMPLATES: dict[str, dict[str, list[str]]] = {
    "pcf": {
        "high": [
            "{tone} 핵심 컬러와 잘 어울려서 피부톤이 한층 밝아 보여요",
            "{tone} 톤에 딱 맞는 색상 조합이에요",
        ],
        "mid": [
            "퍼스널컬러와 비교적 잘 어울리는 색상 구성이에요",
            "전체적으로 톤에 무난하게 어울리는 컬러예요",
        ],
    },
    "of": {
        "high": [
            "{tpo} 룩에 적합한 스타일링이에요",
            "{tpo} 상황에 딱 맞는 코디예요",
        ],
        "mid": [
            "다양한 상황에 무난하게 활용할 수 있는 스타일이에요",
            "여러 상황에 두루 어울리는 코디예요",
        ],
    },
    "ch": {
        "high": [
            "메인-서브-포인트 컬러가 균형 있게 조화를 이뤄요",
            "색상 배합이 세련되고 안정감 있어요",
        ],
        "mid": [
            "전체적으로 안정감 있는 색상 배합이에요",
            "컬러 구성이 무난하게 어울려요",
        ],
    },
    "pe": {
        "high": [
            "예산 범위 내에서 가성비 좋은 조합이에요",
            "합리적인 가격대의 스타일링이에요",
        ],
        "mid": [
            "가격 대비 만족스러운 구성이에요",
            "전체적으로 가격 밸런스가 적절해요",
        ],
    },
    "sf": {
        "high": [
            "스타일 조화가 뛰어난 코디예요",
            "실루엣 밸런스가 좋은 세련된 코디예요",
        ],
        "mid": [
            "전체적으로 무난한 스타일 구성이에요",
            "아이템 간 스타일이 자연스럽게 어우러져요",
        ],
    },
}


def _select_top_axes(
    scores: dict[str, float],
    weights: dict[str, float] | None = None,
    n: int = 2,
) -> list[tuple[str, float, float]]:
    """가중 기여도 상위 n개 축을 선택한다.

    Returns:
        [(axis, raw_score, contribution), ...] 기여도 내림차순
    """
    w = weights or DEFAULT_WEIGHTS
    axes = ["pcf", "of", "ch", "pe", "sf"]

    contributions = []
    for axis in axes:
        raw = scores.get(axis, 0.0)
        contrib = raw * w.get(axis, 0.0)
        contributions.append((axis, raw, contrib))

    contributions.sort(key=lambda x: x[2], reverse=True)
    return contributions[:n]


def generate_reasons(
    scores: dict[str, float],
    user_tone_id: str = "",
    user_tpo_list: list[str] | None = None,
    weights: dict[str, float] | None = None,
) -> list[str]:
    """5축 가중 기여도 기반 추천 이유 2줄을 생성한다.

    Args:
        scores: 5축 점수 딕셔너리 (pcf, of, ch, pe, sf)
        user_tone_id: 사용자 톤 ID (PCF 템플릿용)
        user_tpo_list: 사용자 TPO 리스트 (OF 템플릿용)
        weights: 개인화 가중치 (없으면 기본 가중치)

    Returns:
        2개의 추천 이유 문자열 리스트
    """
    if user_tpo_list is None:
        user_tpo_list = []

    top_axes = _select_top_axes(scores, weights, n=2)
    reasons: list[str] = []

    for axis, raw_score, _ in top_axes:
        level = "high" if raw_score >= 75 else "mid"
        templates = TEMPLATES[axis][level]

        # 첫 번째 템플릿 사용 (동일 축 반복 방지용 인덱스)
        idx = 0 if len(reasons) == 0 else min(1, len(templates) - 1)
        template = templates[idx]

        # 변수 치환
        tone_name = TONE_NAMES_KO.get(user_tone_id, "내 퍼스널컬러")
        tpo_name = TPO_NAMES_KO.get(user_tpo_list[0], "일상") if user_tpo_list else "일상"

        reason = template.format(tone=tone_name, tpo=tpo_name)
        reasons.append(reason)

    return reasons
