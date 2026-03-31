"""Task 2.10 — 추천 이유 생성 테스트."""

import pytest
from app.services.reason_generator import (
    generate_reasons,
    _select_top_axes,
    TONE_NAMES_KO,
    TPO_NAMES_KO,
)


class TestSelectTopAxes:

    def test_pcf_highest(self):
        """PCF 기여도 최고 → 첫 번째 선택."""
        scores = {"pcf": 95, "of": 60, "ch": 50, "pe": 40, "sf": 70}
        top = _select_top_axes(scores)
        assert top[0][0] == "pcf"

    def test_of_highest(self):
        """OF 기여도 최고."""
        scores = {"pcf": 30, "of": 100, "ch": 50, "pe": 40, "sf": 30}
        top = _select_top_axes(scores)
        assert top[0][0] == "of"

    def test_returns_two(self):
        scores = {"pcf": 90, "of": 80, "ch": 70, "pe": 60, "sf": 85}
        top = _select_top_axes(scores)
        assert len(top) == 2

    def test_tie_breaking(self):
        """동점 시 두 축 모두 포함."""
        # pcf*0.25=25, sf*0.25=25 → 동점, 둘 다 상위
        scores = {"pcf": 100, "of": 0, "ch": 0, "pe": 0, "sf": 100}
        top = _select_top_axes(scores)
        axes = {t[0] for t in top}
        assert "pcf" in axes
        assert "sf" in axes

    def test_contribution_weighted(self):
        """기여도 = 점수 × 가중치."""
        scores = {"pcf": 80, "of": 90, "ch": 70, "pe": 60, "sf": 80}
        top = _select_top_axes(scores)
        # pcf: 80*0.25=20, of: 90*0.20=18, sf: 80*0.25=20
        axes = [t[0] for t in top]
        assert "pcf" in axes or "sf" in axes


class TestGenerateReasons:

    def test_returns_two_reasons(self):
        scores = {"pcf": 90, "of": 80, "ch": 70, "pe": 60, "sf": 85}
        reasons = generate_reasons(scores, "summer_cool_soft", ["office"])
        assert len(reasons) == 2
        assert all(isinstance(r, str) for r in reasons)

    def test_pcf_high_includes_tone_name(self):
        """PCF high → 톤 이름 포함."""
        scores = {"pcf": 95, "of": 30, "ch": 30, "pe": 30, "sf": 30}
        reasons = generate_reasons(scores, "summer_cool_soft", ["office"])
        assert "여름쿨소프트" in reasons[0]

    def test_of_high_includes_tpo(self):
        """OF high → TPO 이름 포함."""
        scores = {"pcf": 30, "of": 95, "ch": 30, "pe": 30, "sf": 30}
        reasons = generate_reasons(scores, "summer_cool_soft", ["date"])
        # OF가 최고 기여
        has_tpo = any("데이트" in r for r in reasons)
        assert has_tpo

    def test_mid_template_under_75(self):
        """75점 미만 → mid 템플릿 (적극적 표현 아님)."""
        scores = {"pcf": 60, "of": 50, "ch": 40, "pe": 50, "sf": 60}
        reasons = generate_reasons(scores, "summer_cool_soft", ["office"])
        # mid 템플릿은 "핵심 컬러"나 "딱 맞는" 같은 적극 표현 없음
        assert all("핵심 컬러" not in r for r in reasons)

    def test_high_template_over_75(self):
        """75점 이상 → high 템플릿."""
        scores = {"pcf": 95, "of": 30, "ch": 30, "pe": 30, "sf": 30}
        reasons = generate_reasons(scores, "summer_cool_soft")
        # PCF high 템플릿
        assert any("핵심 컬러" in r or "딱 맞는" in r for r in reasons)

    def test_no_tone_id_fallback(self):
        """톤 ID 없으면 '내 퍼스널컬러' 사용."""
        scores = {"pcf": 95, "of": 30, "ch": 30, "pe": 30, "sf": 30}
        reasons = generate_reasons(scores, "", [])
        assert any("내 퍼스널컬러" in r for r in reasons)

    def test_no_tpo_fallback(self):
        """TPO 없으면 '일상' 사용."""
        scores = {"pcf": 30, "of": 95, "ch": 30, "pe": 30, "sf": 30}
        reasons = generate_reasons(scores, "summer_cool_soft", [])
        has_daily = any("일상" in r for r in reasons)
        has_generic = any("다양한 상황" in r or "여러 상황" in r for r in reasons)
        assert has_daily or has_generic

    def test_all_tone_names_mapped(self):
        """12톤 모두 한글 매핑 존재."""
        assert len(TONE_NAMES_KO) == 12

    def test_empty_scores(self):
        """빈 점수 → 에러 없이 2줄 반환."""
        scores = {"pcf": 0, "of": 0, "ch": 0, "pe": 0, "sf": 0}
        reasons = generate_reasons(scores)
        assert len(reasons) == 2

    def test_sf_highest(self):
        """SF 최고 기여 → SF 템플릿."""
        scores = {"pcf": 30, "of": 30, "ch": 30, "pe": 30, "sf": 95}
        reasons = generate_reasons(scores)
        has_sf = any("스타일" in r or "실루엣" in r for r in reasons)
        assert has_sf

    def test_pe_highest(self):
        """PE 최고 기여 → PE 템플릿."""
        scores = {"pcf": 30, "of": 30, "ch": 30, "pe": 95, "sf": 30}
        reasons = generate_reasons(scores)
        has_pe = any("예산" in r or "가격" in r or "가성비" in r for r in reasons)
        assert has_pe

    def test_ch_highest(self):
        """CH 최고 기여 → CH 템플릿."""
        scores = {"pcf": 30, "of": 30, "ch": 95, "pe": 30, "sf": 30}
        reasons = generate_reasons(scores)
        has_ch = any("컬러" in r or "색상" in r or "조화" in r for r in reasons)
        assert has_ch
