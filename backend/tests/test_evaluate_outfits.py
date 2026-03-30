"""evaluate_outfits.py 단위 테스트."""

import pytest

from backend.scripts.evaluate_outfits import (
    WEIGHTS,
    _rule_based_score,
    calculate_weighted_score,
    evaluate_batch,
    format_items,
)


def _outfit(oid="o1", tpo="commute", items=None):
    return {
        "outfit_id": oid,
        "designed_tpo": tpo,
        "designed_moods": ["classic"],
        "items": items or [
            {"category": "셔츠", "name": "테스트 셔츠", "price": 30000, "formality": 4},
            {"category": "슬랙스", "name": "테스트 슬랙스", "price": 40000, "formality": 4},
        ],
    }


class TestFormatItems:
    def test_basic(self):
        items = [{"category": "니트", "name": "캐시미어 니트", "price": 59000}]
        result = format_items(items)
        assert "니트" in result
        assert "59,000" in result

    def test_empty(self):
        assert format_items([]) == ""


class TestCalculateWeightedScore:
    def test_all_fives(self):
        scores = {k: 5 for k in WEIGHTS}
        assert calculate_weighted_score(scores) == 5.0

    def test_all_ones(self):
        scores = {k: 1 for k in WEIGHTS}
        assert calculate_weighted_score(scores) == 1.0

    def test_mixed(self):
        scores = {
            "style_cohesion": 5,
            "silhouette_balance": 4,
            "trend_relevance": 3,
            "material_harmony": 3,
            "overall_styling": 3,
        }
        expected = 5*0.30 + 4*0.25 + 3*0.15 + 3*0.15 + 3*0.15
        assert abs(calculate_weighted_score(scores) - expected) < 0.01


class TestRuleBasedScore:
    def test_consistent_formality(self):
        outfit = _outfit(items=[
            {"category": "셔츠", "formality": 4},
            {"category": "슬랙스", "formality": 4},
        ])
        scores = _rule_based_score(outfit)
        assert scores["style_cohesion"] == 5  # 편차 0

    def test_inconsistent_formality(self):
        outfit = _outfit(items=[
            {"category": "후드", "formality": 1},
            {"category": "힐", "formality": 5},
        ])
        scores = _rule_based_score(outfit)
        assert scores["style_cohesion"] == 1  # 편차 4


class TestEvaluateBatch:
    def test_dry_run(self):
        outfits = [_outfit("o1"), _outfit("o2")]
        passed, stats = evaluate_batch(outfits, min_score=3, dry_run=True)
        assert stats["total"] == 2
        assert stats["passed"] + stats["failed"] == 2
        assert all(o.get("llm_quality_score") is not None for o in passed)

    def test_min_score_filter(self):
        # 포멀도 불일치로 낮은 점수 생성
        bad_outfit = _outfit("bad", items=[
            {"category": "후드", "formality": 1},
            {"category": "힐", "formality": 5},
            {"category": "레깅스", "formality": 1},
        ])
        good_outfit = _outfit("good", items=[
            {"category": "셔츠", "formality": 4},
            {"category": "슬랙스", "formality": 4},
            {"category": "로퍼", "formality": 4},
        ])
        passed, stats = evaluate_batch([bad_outfit, good_outfit], min_score=3, dry_run=True)
        # good은 통과해야 함
        assert any(o["outfit_id"] == "good" for o in passed)
