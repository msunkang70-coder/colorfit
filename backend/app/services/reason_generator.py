"""
추천 이유 생성기 v2 — core / evidence / risk_guard 3파트 구조.

각 파트는 문자열 1개. 단일 결정 UX에 맞게 최소화.
"""

from __future__ import annotations

from typing import TypedDict

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
# 카테고리 구분
# ──────────────────────────────────────────────
UPPER_CATEGORIES = {"셔츠", "블라우스", "니트", "스웨터", "티셔츠", "맨투맨", "후드", "자켓", "코트", "가디건", "조끼", "탑"}
LOWER_CATEGORIES = {"슬랙스", "팬츠", "스커트", "청바지", "반바지", "와이드팬츠", "레깅스", "치마"}
ONEPIECE_CATEGORIES = {"원피스", "점프수트"}

# ──────────────────────────────────────────────
# TPO별 안전 범위 설명
# ──────────────────────────────────────────────
TPO_SAFE_DESC: dict[str, str] = {
    "commute": "오피스에서 가장 보편적인 스타일 범위",
    "office": "오피스에서 가장 보편적인 스타일 범위",
    "interview": "면접에서 안전한 정장 계열 범위",
    "campus": "캠퍼스에서 자연스러운 캐주얼 범위",
    "date": "데이트에서 호감을 주는 스타일 범위",
    "weekend": "주말 외출에 무난한 캐주얼 범위",
    "casual": "일상에서 편안하게 입을 수 있는 범위",
    "daily": "일상에서 편안하게 입을 수 있는 범위",
    "travel": "여행에서 활동적이면서 깔끔한 범위",
    "event": "행사에 격식을 갖추면서 세련된 범위",
    "party": "파티에서 돋보이면서도 과하지 않은 범위",
    "wedding": "웨딩 참석에 격식 있는 범위",
    "workout": "운동에 기능적이면서 스타일리시한 범위",
}


# ──────────────────────────────────────────────
# ReasonResult — 각 파트 문자열 1개
# ──────────────────────────────────────────────
class ReasonResult(TypedDict):
    core: str
    evidence: str
    risk_guard: str


# ──────────────────────────────────────────────
# 헬퍼
# ──────────────────────────────────────────────

def _select_top_axis(
    scores: dict[str, float],
    weights: dict[str, float] | None = None,
) -> tuple[str, float]:
    """가중 기여도 1순위 축을 선택한다. (axis, raw_score)"""
    w = weights or DEFAULT_WEIGHTS
    best_axis, best_score, best_contrib = "pcf", 0.0, -1.0
    for axis in ("pcf", "of", "ch", "pe", "sf"):
        raw = scores.get(axis, 0.0)
        contrib = raw * w.get(axis, 0.0)
        if contrib > best_contrib:
            best_axis, best_score, best_contrib = axis, raw, contrib
    return best_axis, best_score


def _extract_item_names(items: list[dict]) -> tuple[str, str]:
    """대표 상의/하의 카테고리명 추출."""
    upper = ""
    lower = ""
    for item in items:
        cat = item.get("category", "")
        if cat in ONEPIECE_CATEGORIES:
            return cat, ""
        if not upper and cat in UPPER_CATEGORIES:
            upper = cat
        if not lower and cat in LOWER_CATEGORIES:
            lower = cat
    if not upper and items:
        upper = items[0].get("category", "아이템")
    if not lower and len(items) > 1:
        lower = items[1].get("category", "")
    return upper or "아이템", lower


def _particle(word: str, with_bat: str, without_bat: str) -> str:
    """한글 받침 유무에 따라 조사 선택."""
    if not word:
        return word + with_bat
    last = word[-1]
    if "가" <= last <= "힣":
        if (ord(last) - 0xAC00) % 28 > 0:
            return word + with_bat
    return word + without_bat


# ──────────────────────────────────────────────
# 빌더
# ──────────────────────────────────────────────

def _build_core(
    items: list[dict],
    user_tone_id: str,
    user_tpo_list: list[str],
    scores: dict[str, float] | None = None,
) -> str:
    tone = TONE_NAMES_KO.get(user_tone_id, "내 퍼스널컬러")
    tpo = TPO_NAMES_KO.get(user_tpo_list[0], "데일리") if user_tpo_list else "데일리"

    # 축 1순위에 따라 core 표현 차별화
    if scores:
        axis, _ = _select_top_axis(scores)
        if axis == "pcf":
            return f"{tone}에 딱 맞는 {tpo} 코디"
        if axis == "of":
            return f"{tpo}에 최적화된 깔끔한 조합"
        if axis == "ch":
            return f"색감 조화가 돋보이는 {tpo} 코디"
        if axis == "pe":
            return f"가성비 좋은 {tpo} 코디"
        if axis == "sf":
            return f"실루엣이 깔끔한 {tpo} 조합"

    upper, lower = _extract_item_names(items)
    if upper and lower:
        return f"{upper} + {lower} — {tone} {tpo}룩"
    if upper:
        return f"{upper} — {tone} {tpo}룩"
    return f"{tone} {tpo}룩"


def _build_evidence(
    scores: dict[str, float],
    items: list[dict],
    user_tone_id: str,
    user_tpo_list: list[str],
    weights: dict[str, float] | None = None,
    variant: int = 0,
) -> str:
    """1순위 축 기반 설득 문장 1개. variant로 문구 변형."""
    axis, raw = _select_top_axis(scores, weights)
    tone = TONE_NAMES_KO.get(user_tone_id, "내 퍼스널컬러")
    tpo = TPO_NAMES_KO.get(user_tpo_list[0], "데일리") if user_tpo_list else "데일리"
    upper, lower = _extract_item_names(items)
    high = raw >= 75
    v = variant % 3

    if axis == "pcf":
        if high and upper:
            opts = [
                f"{upper}의 색감이 {tone} 톤과 자연스럽게 어울려서 피부가 밝아 보여요",
                f"{tone}의 시원한 톤에 맞춘 색상이라 얼굴이 화사해 보여요",
                f"피부 톤과 조화로운 색상 선택으로 자연스러운 분위기가 나요",
            ]
            return opts[v]
        return f"전체적으로 {tone}에 어울리는 색상 구성이에요"

    if axis == "of":
        if high:
            opts = [
                f"{tpo} 상황에 맞는 격식과 분위기를 갖춘 조합이에요",
                f"{tpo}에 딱 맞는 무드를 연출할 수 있는 스타일이에요",
                f"{tpo} 자리에서 자연스럽게 어울리는 코디예요",
            ]
            return opts[v]
        return f"다양한 상황에 활용하기 좋은 범용적인 스타일이에요"

    if axis == "ch":
        if high and upper and lower:
            opts = [
                f"{_particle(upper, '과', '와')} {lower}의 색상 배합이 안정적이고 세련돼요",
                f"아이템 간 컬러 매칭이 자연스러워서 완성도가 높아요",
                f"색감이 통일감 있게 어우러져서 깔끔한 인상을 줘요",
            ]
            return opts[v]
        return f"아이템 간 색상 조화가 좋은 코디예요"

    if axis == "pe":
        total = sum(it.get("price", 0) for it in items)
        if high and total:
            opts = [
                f"총 {total:,}원으로 예산 범위 안에서 가성비 좋은 조합이에요",
                f"합리적인 가격에 스타일까지 챙긴 효율적인 코디예요",
                f"부담 없는 가격대로 구성된 실용적인 조합이에요",
            ]
            return opts[v]
        return f"가격 대비 만족스러운 구성이에요"

    if axis == "sf":
        if high and upper and lower:
            opts = [
                f"{_particle(upper, '과', '와')} {lower}의 실루엣 밸런스가 좋아서 깔끔한 라인이 나와요",
                f"상의와 하의의 핏 조합이 자연스러워서 체형이 깔끔하게 보여요",
                f"아이템 간 스타일이 잘 맞아서 세련된 분위기가 나요",
            ]
            return opts[v]
        return f"아이템 간 스타일 조화가 좋은 코디예요"

    return f"{tone}에 어울리는 코디예요"


def _build_risk_guard(
    scores: dict[str, float],
    items: list[dict],
    user_tpo_list: list[str],
) -> str:
    """안전 근거 1개. 우선순위: 색상안전 > 포멀도안전 > TPO안전 > fallback."""
    upper, lower = _extract_item_names(items)

    # 색상 안전
    if scores.get("ch", 0) >= 70 and upper and lower:
        return f"{_particle(upper, '과', '와')} {_particle(lower, '은', '는')} 색상 대비가 적절해서 튀거나 칙칙해 보일 가능성이 낮아요"

    # 포멀도 안전
    formalities = [it.get("formality", 3) for it in items if it.get("formality")]
    if len(formalities) >= 2:
        avg = sum(formalities) / len(formalities)
        std = (sum((f - avg) ** 2 for f in formalities) / len(formalities)) ** 0.5
        if std <= 1.0:
            return "아이템 간 격식 수준이 비슷해서 어색한 조합이 될 가능성이 낮아요"

    # TPO 안전
    if scores.get("of", 0) >= 60 and user_tpo_list:
        desc = TPO_SAFE_DESC.get(user_tpo_list[0], "일상에서 편안하게 입을 수 있는 범위")
        return f"이 조합은 {desc} 안에 있어요"

    return "검증된 색상 조합과 스타일 구성으로 실패 가능성이 낮은 코디예요"


# ──────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────

def generate_reasons(
    scores: dict[str, float],
    items: list[dict] | None = None,
    user_tone_id: str = "",
    user_tpo_list: list[str] | None = None,
    weights: dict[str, float] | None = None,
) -> ReasonResult:
    """코디 결정 이유 3파트를 생성한다. 각 파트 문자열 1개."""
    if items is None:
        items = []
    if user_tpo_list is None:
        user_tpo_list = []

    # variant: 아이템 가격 합으로 해시 생성 → 같은 코디라도 다른 문구 변형
    variant = sum(it.get("price", 0) for it in items) % 3

    return ReasonResult(
        core=_build_core(items, user_tone_id, user_tpo_list, scores),
        evidence=_build_evidence(scores, items, user_tone_id, user_tpo_list, weights, variant),
        risk_guard=_build_risk_guard(scores, items, user_tpo_list),
    )
