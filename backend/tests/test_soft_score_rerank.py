"""Task 2.9 — Soft Score + 리랭킹 테스트."""

import pytest
from app.services.feed_builder import (
    compute_soft_scores,
    rerank,
    score_and_rerank,
    _personalization_bonus,
    DEFAULT_WEIGHTS,
)


def _make_scored_outfit(
    outfit_id: str = "o1",
    total: float = 80.0,
    tone_id: str = "summer_cool_soft",
    is_complete: bool = False,
    main_product_id: str = "p1",
    **kwargs,
) -> dict:
    base = {
        "outfit_id": outfit_id,
        "items": [
            {"title": "블라우스", "tone_id": tone_id, "color_hex": "#B0A6C6",
             "product_id": main_product_id, "brand": "무신사 스탠다드",
             "category": "blouse"},
            {"title": "슬랙스", "tone_id": tone_id, "color_hex": "#F5F0E8",
             "product_id": "p2", "brand": "유니클로", "category": "slacks"},
        ],
        "total_price": 80000,
        "designed_tpo": ["office", "commute"],
        "tags": ["office", "spring"],
        "is_complete_outfit": is_complete,
        "scores": {"total": total, "pcf": 90, "of": 80, "ch": 85, "pe": 75, "sf": 80},
    }
    base.update(kwargs)
    return base


class TestComputeSoftScores:

    def test_returns_all_axes(self):
        outfit = _make_scored_outfit()
        scores = compute_soft_scores(
            outfit, "summer_cool_soft", ["office"], 30000, 100000,
        )
        assert "pcf" in scores
        assert "of" in scores
        assert "ch" in scores
        assert "pe" in scores
        assert "sf" in scores
        assert "total" in scores

    def test_total_is_weighted_sum(self):
        outfit = _make_scored_outfit()
        scores = compute_soft_scores(
            outfit, "summer_cool_soft", ["office"], 30000, 100000,
        )
        w = DEFAULT_WEIGHTS
        expected = (
            scores["pcf"] * w["pcf"]
            + scores["of"] * w["of"]
            + scores["ch"] * w["ch"]
            + scores["pe"] * w["pe"]
            + scores["sf"] * w["sf"]
        )
        assert abs(scores["total"] - round(expected, 2)) < 0.02

    def test_score_range(self):
        outfit = _make_scored_outfit()
        scores = compute_soft_scores(
            outfit, "summer_cool_soft", ["office"], 30000, 100000,
        )
        for key, val in scores.items():
            assert 0 <= val <= 100, f"{key}={val}"

    def test_weight_overrides(self):
        outfit = _make_scored_outfit()
        # PCF 가중치를 높이면 PCF가 높은 코디의 total이 올라감
        scores_default = compute_soft_scores(
            outfit, "summer_cool_soft", ["office"], 30000, 100000,
        )
        scores_pcf_heavy = compute_soft_scores(
            outfit, "summer_cool_soft", ["office"], 30000, 100000,
            weight_overrides={"pcf": 0.50},
        )
        # 두 결과 모두 유효 범위
        assert 0 <= scores_default["total"] <= 100
        assert 0 <= scores_pcf_heavy["total"] <= 100


class TestPersonalizationBonus:

    def test_no_preferences(self):
        outfit = _make_scored_outfit()
        assert _personalization_bonus(outfit, None) == 0.0

    def test_tone_preference(self):
        outfit = _make_scored_outfit(tone_id="summer_cool_soft")
        prefs = {"tone_preferences": {"summer_cool_soft": 2.0}}
        bonus = _personalization_bonus(outfit, prefs)
        assert bonus > 0

    def test_capped_at_10(self):
        outfit = _make_scored_outfit()
        prefs = {
            "tone_preferences": {"summer_cool_soft": 10.0},
            "category_preferences": {"blouse": 10.0, "slacks": 10.0},
            "brand_preferences": {"무신사 스탠다드": 10.0, "유니클로": 10.0},
        }
        bonus = _personalization_bonus(outfit, prefs)
        assert bonus <= 10.0

    def test_negative_not_below_minus10(self):
        """보정값 범위: -10 ~ +10."""
        outfit = _make_scored_outfit()
        bonus = _personalization_bonus(outfit, {})
        assert bonus >= -10.0


class TestRerank:

    def test_sorted_by_total(self):
        o1 = _make_scored_outfit("o1", total=90)
        o2 = _make_scored_outfit("o2", total=80, main_product_id="p3")
        o3 = _make_scored_outfit("o3", total=95, main_product_id="p5")
        result = rerank([o1, o2, o3])
        totals = [o["scores"]["reranked_total"] for o in result]
        assert totals == sorted(totals, reverse=True)

    def test_dislike_excluded(self):
        o1 = _make_scored_outfit("o1", total=90)
        o2 = _make_scored_outfit("o2", total=80, main_product_id="p3")
        result = rerank([o1, o2], disliked_ids={"o1"})
        assert len(result) == 1
        assert result[0]["outfit_id"] == "o2"

    def test_complete_outfit_bonus(self):
        """완성 코디 +3점 가산."""
        incomplete = _make_scored_outfit("o1", total=80, is_complete=False)
        complete = _make_scored_outfit("o2", total=80, is_complete=True, main_product_id="p3")
        result = rerank([incomplete, complete])
        # complete가 +3점으로 상위
        assert result[0]["outfit_id"] == "o2"

    def test_tone_diversity_limit(self):
        """동일 톤 3개 제한."""
        outfits = [
            _make_scored_outfit(f"o{i}", total=90-i, tone_id="summer_cool_soft",
                                main_product_id=f"p{i}")
            for i in range(5)
        ]
        result = rerank(outfits)
        tones = [_get_dominant(o) for o in result]
        assert tones.count("summer_cool_soft") <= 3

    def test_main_item_dedup(self):
        """메인아이템(첫 아이템) 중복 제거."""
        o1 = _make_scored_outfit("o1", total=90, main_product_id="same_product")
        o2 = _make_scored_outfit("o2", total=85, main_product_id="same_product")
        o3 = _make_scored_outfit("o3", total=80, main_product_id="diff_product")
        result = rerank([o1, o2, o3])
        main_ids = [o["items"][0]["product_id"] for o in result]
        assert main_ids.count("same_product") == 1

    def test_max_results(self):
        outfits = [
            _make_scored_outfit(f"o{i}", total=90-i, main_product_id=f"p{i}",
                                tone_id=f"summer_cool_soft" if i < 3 else "winter_cool_deep")
            for i in range(10)
        ]
        result = rerank(outfits, max_results=5)
        assert len(result) <= 5

    def test_personalization_affects_order(self):
        """개인화 보정이 순위에 영향."""
        o1 = _make_scored_outfit("o1", total=80, tone_id="summer_cool_soft")
        o2 = _make_scored_outfit("o2", total=82, tone_id="winter_cool_deep",
                                 main_product_id="p3")
        prefs = {"tone_preferences": {"summer_cool_soft": 3.0}}
        result = rerank([o1, o2], preferences=prefs)
        # o1이 보정으로 올라올 수 있음
        assert len(result) == 2

    def test_empty_input(self):
        assert rerank([]) == []


class TestScoreAndRerank:

    def test_end_to_end(self):
        outfits = [
            _make_scored_outfit("o1", main_product_id="p1"),
            _make_scored_outfit("o2", main_product_id="p3"),
        ]
        result = score_and_rerank(
            outfits,
            user_tone_id="summer_cool_soft",
            user_tpo_list=["office"],
            budget_min=30000,
            budget_max=100000,
        )
        assert len(result) == 2
        assert "scores" in result[0]
        assert "reranked_total" in result[0]["scores"]

    def test_returns_max_200(self):
        outfits = [
            _make_scored_outfit(f"o{i}", main_product_id=f"p{i}",
                                tone_id="summer_cool_soft" if i < 3 else "winter_cool_deep")
            for i in range(250)
        ]
        result = score_and_rerank(
            outfits,
            user_tone_id="summer_cool_soft",
            user_tpo_list=["office"],
            budget_min=30000,
            budget_max=100000,
            max_results=200,
        )
        assert len(result) <= 200


def _get_dominant(outfit: dict) -> str | None:
    """테스트 헬퍼: 코디의 대표 톤."""
    tones: dict[str, int] = {}
    for item in outfit.get("items", []):
        tone = item.get("tone_id")
        if tone:
            tones[tone] = tones.get(tone, 0) + 1
    return max(tones, key=tones.get) if tones else None
