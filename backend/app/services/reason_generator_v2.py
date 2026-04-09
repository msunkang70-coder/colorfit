"""Reason Generator v2 — core / risk_guard / situation 3파트."""

from __future__ import annotations

from typing import TypedDict

TONE_KR = {
    "spring_warm_light": "봄웜라이트", "spring_warm_bright": "봄웜브라이트",
    "spring_warm_mute": "봄웜뮤트", "summer_cool_light": "여름쿨라이트",
    "summer_cool_soft": "여름쿨소프트", "summer_cool_mute": "여름쿨뮤트",
    "autumn_warm_deep": "가을웜딥", "autumn_warm_bright": "가을웜브라이트",
    "autumn_warm_mute": "가을웜뮤트", "winter_cool_deep": "겨울쿨딥",
    "winter_cool_bright": "겨울쿨브라이트", "winter_cool_light": "겨울쿨라이트",
}

TPO_KR = {
    "commute": "출근", "interview": "면접", "date": "데이트",
    "campus": "캠퍼스", "weekend": "주말", "travel": "여행",
    "event": "행사", "workout": "운동",
}

STYLE_KR = {
    "casual": "캐주얼", "formal": "포멀", "minimal": "미니멀",
    "feminine": "페미닌", "sporty": "스포티", "classic": "클래식",
    "street": "스트릿", "dandy": "댄디",
}

# ── Core 템플릿 ──

CORE_BY_TPO = {
    "interview": [
        "면접관에게 신뢰감을 주는 깔끔한 {style} 코디",
        "{tone} 톤에 맞춘 단정한 면접 코디",
    ],
    "commute": [
        "오피스에서 세련되게 보이는 {style} 코디",
        "출근길에 자신감을 주는 균형 잡힌 조합",
    ],
    "date": [
        "부담 없이 좋은 인상을 남기는 {style} 코디",
        "자연스러운 매력을 살린 데이트 코디",
    ],
    "campus": [
        "캠퍼스에서 세련되게 보이는 {style} 코디",
        "편안하면서도 감각적인 캠퍼스 룩",
    ],
    "weekend": [
        "편안하면서도 스타일 있는 주말 코디",
        "일상에서 자연스럽게 돋보이는 {style} 조합",
    ],
    "travel": [
        "활동적이면서 스타일을 놓치지 않는 여행 코디",
        "여행 중 편안하고 멋진 {style} 룩",
    ],
    "event": [
        "행사에서 품격을 유지하는 {style} 코디",
        "격식 있는 자리에 어울리는 세련된 조합",
    ],
    "workout": [
        "운동에 최적화된 기능적이면서 깔끔한 코디",
        "활동성과 스타일을 모두 잡은 운동복 조합",
    ],
}

CORE_BY_AXIS = {
    "color": [
        "{tone}에 어울리는 색감으로 구성한 코디",
        "자연스러운 색상 조화가 돋보이는 조합",
    ],
    "fit": [
        "체형 밸런스를 살린 실루엣 구성",
        "상하의 비율이 좋아 보이는 핏 조합",
    ],
    "style": [
        "아이템 간 스타일이 통일된 완성도 높은 코디",
        "{style} 무드로 일관된 세련된 조합",
    ],
}

# ── Risk Guard 템플릿 ──

RISK_SAFE = [
    "아이템 간 격식 수준과 스타일이 일관되어 실패 가능성이 낮은 코디예요",
    "검증된 색상 조합과 균형 잡힌 실루엣으로 안정적인 코디예요",
]

RISK_MILD = [
    "전체적으로 무난하지만, {factor}에 살짝 주의하면 더 좋아요",
]

RISK_WARN = [
    "{factor}로 인해 상황에 따라 어색할 수 있어요",
]

# ── Situation 템플릿 ──

TPO_SITUATION = {
    "interview": "채용 면접, 인턴 면접, 승진 면접",
    "commute": "평일 출근, 클라이언트 미팅, 팀 회의",
    "date": "저녁 데이트, 카페 데이트, 전시회",
    "weekend": "친구 약속, 쇼핑, 브런치",
    "campus": "수업, 도서관, 동아리 활동",
    "event": "결혼식 하객, 파티, 시상식",
    "travel": "국내 여행, 해외 여행, 당일치기",
    "workout": "헬스장, 러닝, 요가",
}


class ReasonResult(TypedDict):
    core: str
    risk_guard: str
    situation: str


def _select_top_axis(scores: dict[str, float]) -> str:
    """risk/final 제외, 가중 기여가 가장 큰 축."""
    weights = {"tpo": 0.30, "fit": 0.15, "color": 0.20, "style": 0.20}
    best, best_val = "tpo", 0.0
    for ax, w in weights.items():
        val = scores.get(ax, 0) * w
        if val > best_val:
            best, best_val = ax, val
    return best


def _particle(word: str) -> str:
    """한글 조사 처리 (와/과)."""
    if not word:
        return "과"
    code = ord(word[-1]) - 0xAC00
    if code < 0 or code > 11171:
        return "과"
    return "과" if code % 28 else "와"


def generate_reasons_v2(
    scores: dict[str, float],
    items: list[dict] | None = None,
    user_tone_id: str = "",
    user_tpo_list: list[str] | None = None,
) -> ReasonResult:
    """3파트 추천 사유 생성."""
    if items is None:
        items = []
    if user_tpo_list is None:
        user_tpo_list = []

    variant = sum(it.get("price", 0) for it in items) % 3
    tone_name = TONE_KR.get(user_tone_id, "")
    tpo_key = user_tpo_list[0].lower() if user_tpo_list else ""
    tpo_name = TPO_KR.get(tpo_key, tpo_key)

    # 아이템 분류
    upper = next((it.get("category", "") for it in items
                   if it.get("category", "") in {"셔츠", "블라우스", "니트", "맨투맨", "후드", "티셔츠"}), "")
    style_tag = ""
    for it in items:
        if it.get("style_tag"):
            style_tag = STYLE_KR.get(it["style_tag"], it["style_tag"])
            break

    top_axis = _select_top_axis(scores)

    # ── Core ──
    templates = CORE_BY_TPO.get(tpo_key, CORE_BY_AXIS.get(top_axis, ["{style} 코디"]))
    tmpl = templates[variant % len(templates)]
    core = tmpl.format(tone=tone_name or "퍼스널컬러", style=style_tag or "추천", tpo=tpo_name)

    # ── Risk Guard ──
    risk_val = scores.get("risk", 0)
    if risk_val >= -3:
        risk_guard = RISK_SAFE[variant % len(RISK_SAFE)]
    elif risk_val >= -10:
        factor = _detect_risk_factor(scores)
        risk_guard = RISK_MILD[0].format(factor=factor)
    else:
        factor = _detect_risk_factor(scores)
        risk_guard = RISK_WARN[0].format(factor=factor)

    # ── Situation ──
    situation = TPO_SITUATION.get(tpo_key, "일상 및 외출")

    return ReasonResult(core=core, risk_guard=risk_guard, situation=situation)


def _detect_risk_factor(scores: dict) -> str:
    """가장 낮은 축 기반 리스크 요인 추출."""
    axes = {"tpo": "TPO 적합도", "fit": "핏 밸런스", "color": "색상 조합", "style": "스타일 일관성"}
    worst = min(axes.keys(), key=lambda a: scores.get(a, 100))
    return axes[worst]
