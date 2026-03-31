"""Task 2.10v2 — 결정 이유 생성 테스트 (3파트, 각 문자열 1개)."""

import pytest
from app.services.reason_generator import (
    generate_reasons,
    _select_top_axis,
    _build_core,
    _build_evidence,
    _build_risk_guard,
    _particle,
    ReasonResult,
    TONE_NAMES_KO,
)


class TestParticle:

    def test_no_batchim(self):
        assert _particle("니트", "과", "와") == "니트와"
        assert _particle("코트", "과", "와") == "코트와"

    def test_with_batchim(self):
        assert _particle("원피스", "과", "와") == "원피스와"

    def test_eun_neun(self):
        assert _particle("슬랙스", "은", "는") == "슬랙스는"

    def test_empty(self):
        assert _particle("", "과", "와") == "과"


class TestSelectTopAxis:

    def test_pcf_highest(self):
        scores = {"pcf": 95, "of": 60, "ch": 50, "pe": 40, "sf": 70}
        axis, _ = _select_top_axis(scores)
        assert axis == "pcf"

    def test_of_highest(self):
        scores = {"pcf": 30, "of": 100, "ch": 50, "pe": 40, "sf": 30}
        axis, _ = _select_top_axis(scores)
        assert axis == "of"

    def test_returns_score(self):
        scores = {"pcf": 90, "of": 80, "ch": 70, "pe": 60, "sf": 85}
        _, raw = _select_top_axis(scores)
        assert raw > 0


class TestBuildCore:

    def test_upper_and_lower(self):
        items = [{"category": "니트"}, {"category": "슬랙스"}]
        core = _build_core(items, "spring_warm_light", ["commute"])
        assert "니트" in core
        assert "슬랙스" in core
        assert "봄웜라이트" in core

    def test_onepiece(self):
        items = [{"category": "원피스"}]
        core = _build_core(items, "summer_cool_soft", ["date"])
        assert "원피스" in core

    def test_empty(self):
        core = _build_core([], "", [])
        assert "내 퍼스널컬러" in core


class TestBuildEvidence:

    def test_returns_string(self):
        scores = {"pcf": 90, "of": 80, "ch": 70, "pe": 60, "sf": 85}
        ev = _build_evidence(scores, [{"category": "니트"}], "spring_warm_light", ["commute"])
        assert isinstance(ev, str)
        assert len(ev) > 0

    def test_pcf_high_mentions_tone(self):
        scores = {"pcf": 95, "of": 30, "ch": 30, "pe": 30, "sf": 30}
        ev = _build_evidence(scores, [{"category": "니트"}], "summer_cool_soft", ["office"])
        assert "여름쿨소프트" in ev

    def test_of_high_mentions_tpo(self):
        scores = {"pcf": 30, "of": 95, "ch": 30, "pe": 30, "sf": 30}
        ev = _build_evidence(scores, [{"category": "셔츠"}], "summer_cool_soft", ["date"])
        assert "데이트" in ev

    def test_pe_high_mentions_price(self):
        scores = {"pcf": 30, "of": 30, "ch": 30, "pe": 95, "sf": 30}
        items = [{"category": "니트", "price": 30000}, {"category": "슬랙스", "price": 20000}]
        ev = _build_evidence(scores, items, "spring_warm_light", ["commute"])
        assert "50,000" in ev or "가성비" in ev

    def test_empty_scores(self):
        ev = _build_evidence({}, [], "", [])
        assert isinstance(ev, str)
        assert len(ev) > 0


class TestBuildRiskGuard:

    def test_returns_string(self):
        scores = {"pcf": 90, "of": 80, "ch": 75, "pe": 60, "sf": 85}
        items = [{"category": "니트", "formality": 3}, {"category": "슬랙스", "formality": 4}]
        rg = _build_risk_guard(scores, items, ["commute"])
        assert isinstance(rg, str)
        assert len(rg) > 0

    def test_ch_high_mentions_color(self):
        scores = {"pcf": 50, "of": 50, "ch": 85, "pe": 50, "sf": 50}
        items = [{"category": "니트"}, {"category": "슬랙스"}]
        rg = _build_risk_guard(scores, items, ["commute"])
        assert "색상" in rg or "대비" in rg

    def test_tpo_guard(self):
        scores = {"pcf": 50, "of": 80, "ch": 50, "pe": 50, "sf": 50}
        rg = _build_risk_guard(scores, [{"formality": 3}], ["interview"])
        assert "면접" in rg or "범위" in rg

    def test_fallback(self):
        scores = {"pcf": 30, "of": 30, "ch": 30, "pe": 30, "sf": 30}
        rg = _build_risk_guard(scores, [], [])
        assert len(rg) > 0


class TestGenerateReasons:

    def test_returns_reason_result(self):
        scores = {"pcf": 90, "of": 80, "ch": 70, "pe": 60, "sf": 85}
        items = [{"category": "니트", "price": 35000}, {"category": "슬랙스", "price": 42000}]
        r = generate_reasons(scores, items, "summer_cool_soft", ["office"])
        assert isinstance(r["core"], str)
        assert isinstance(r["evidence"], str)
        assert isinstance(r["risk_guard"], str)
        assert len(r["core"]) > 0
        assert len(r["evidence"]) > 0
        assert len(r["risk_guard"]) > 0

    def test_empty_everything(self):
        r = generate_reasons({})
        assert len(r["core"]) > 0
        assert len(r["evidence"]) > 0
        assert len(r["risk_guard"]) > 0

    def test_all_tone_names(self):
        assert len(TONE_NAMES_KO) == 12

    def test_no_items(self):
        r = generate_reasons({"pcf": 80, "of": 70}, user_tone_id="winter_cool_deep")
        assert isinstance(r["core"], str)
