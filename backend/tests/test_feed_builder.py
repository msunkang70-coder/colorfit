"""Task 2.8 — Hard Filter 체인 테스트."""

import pytest
from app.services.feed_builder import (
    filter_h1_gender,
    filter_h2_budget,
    filter_h3_season,
    filter_h4_tpo,
    filter_h5_brand,
    filter_h6_llm_quality,
    filter_h7_tone,
    apply_hard_filters,
)


def _make_outfit(**kwargs) -> dict:
    """테스트용 코디 헬퍼."""
    base = {
        "items": [
            {"title": "블라우스 아이보리", "brand": "무신사 스탠다드",
             "gender": "female", "tone_id": "summer_cool_soft"},
            {"title": "슬랙스 차콜", "brand": "유니클로",
             "gender": "unisex", "tone_id": "summer_cool_soft"},
        ],
        "total_price": 80000,
        "tags": ["office", "spring"],
        "designed_tpo": ["commute", "office"],
        "llm_quality_score": 4,
    }
    base.update(kwargs)
    return base


class TestH1Gender:

    def test_matching_gender(self):
        assert filter_h1_gender(_make_outfit(), "female") is True

    def test_unisex_passes(self):
        assert filter_h1_gender(_make_outfit(), "male") is False

    def test_no_gender_set(self):
        assert filter_h1_gender(_make_outfit(), "") is True

    def test_all_unisex(self):
        outfit = _make_outfit(items=[
            {"title": "티셔츠", "gender": "unisex"},
        ])
        assert filter_h1_gender(outfit, "male") is True


class TestH2Budget:

    def test_within_budget(self):
        assert filter_h2_budget(_make_outfit(total_price=80000), 100000) is True

    def test_slightly_over(self):
        """1.5배 이내 → 통과."""
        assert filter_h2_budget(_make_outfit(total_price=140000), 100000) is True

    def test_way_over(self):
        """1.5배 초과 → 탈락."""
        assert filter_h2_budget(_make_outfit(total_price=160000), 100000) is False

    def test_no_budget(self):
        assert filter_h2_budget(_make_outfit(total_price=999999), 0) is True


class TestH3Season:

    def test_matching_season(self):
        """봄 태그 + 4월 → 통과."""
        assert filter_h3_season(_make_outfit(tags=["spring"]), 4) is True

    def test_adjacent_season(self):
        """봄 태그 + 6월(여름) → 인접 시즌 통과."""
        assert filter_h3_season(_make_outfit(tags=["spring"]), 6) is True

    def test_opposite_season(self):
        """겨울 태그 + 7월(여름) → 탈락."""
        assert filter_h3_season(_make_outfit(tags=["winter"]), 7) is False

    def test_no_season_tag(self):
        """시즌 태그 없으면 통과."""
        assert filter_h3_season(_make_outfit(tags=["office"]), 7) is True

    def test_travel_bypasses(self):
        """TPO가 travel이면 시즌 필터 완화."""
        assert filter_h3_season(_make_outfit(tags=["winter", "travel"]), 7) is True


class TestH4TPO:

    def test_matching_tpo(self):
        assert filter_h4_tpo(_make_outfit(), ["office"]) is True

    def test_synonym_match(self):
        """commute → {office, commute} 확장."""
        assert filter_h4_tpo(_make_outfit(), ["commute"]) is True

    def test_no_match(self):
        assert filter_h4_tpo(
            _make_outfit(designed_tpo=["workout"]), ["office"]
        ) is False

    def test_empty_user_tpo(self):
        assert filter_h4_tpo(_make_outfit(), []) is True


class TestH5Brand:

    def test_whitelist_brand(self):
        assert filter_h5_brand(_make_outfit()) is True

    def test_no_whitelist_brand(self):
        outfit = _make_outfit(items=[
            {"title": "상품", "brand": "알수없는브랜드XYZ"},
        ])
        assert filter_h5_brand(outfit) is False


class TestH6LLMQuality:

    def test_good_score(self):
        assert filter_h6_llm_quality(_make_outfit(llm_quality_score=4)) is True

    def test_bad_score(self):
        assert filter_h6_llm_quality(_make_outfit(llm_quality_score=2)) is False

    def test_no_score_passes(self):
        """미평가 → 통과 (기본값 5)."""
        outfit = _make_outfit()
        del outfit["llm_quality_score"]
        assert filter_h6_llm_quality(outfit) is True


class TestH7Tone:

    def test_matching_tone(self):
        assert filter_h7_tone(_make_outfit(), "summer_cool_soft") is True

    def test_compatible_tone(self):
        """같은 시즌 호환 톤 → 통과."""
        assert filter_h7_tone(_make_outfit(), "summer_cool_light") is True

    def test_completely_incompatible(self):
        """완전 불일치 + 모든 아이템 반대 톤 → 탈락."""
        outfit = _make_outfit(items=[
            {"title": "상품1", "tone_id": "spring_warm_light", "brand": "무신사 스탠다드", "gender": "female"},
            {"title": "상품2", "tone_id": "spring_warm_bright", "brand": "유니클로", "gender": "unisex"},
        ])
        # winter_cool_deep 사용자에게 봄웜 톤만 있으면 → 호환 60점 미만이면 탈락
        result = filter_h7_tone(outfit, "winter_cool_deep")
        # spring_warm_light vs winter_cool_deep → 40~55점 → 60점 미만 → 호환 아님
        assert result is False

    def test_no_tone_info(self):
        """톤 정보 없으면 통과."""
        outfit = _make_outfit(items=[
            {"title": "상품", "brand": "무신사 스탠다드", "gender": "female"},
        ])
        assert filter_h7_tone(outfit, "winter_cool_deep") is True

    def test_no_user_tone(self):
        assert filter_h7_tone(_make_outfit(), "") is True


class TestApplyHardFilters:

    def test_good_outfit_passes_all(self):
        """좋은 코디 → 전체 통과."""
        outfits = [_make_outfit()]
        result = apply_hard_filters(
            outfits,
            user_gender="female",
            budget_max=200000,
            user_tpo_list=["office"],
            user_tone_id="summer_cool_soft",
            current_month=4,
        )
        assert len(result) == 1

    def test_filters_remove_bad(self):
        """여러 코디 중 부적합한 것들이 제거."""
        good = _make_outfit()
        bad_budget = _make_outfit(total_price=500000)
        bad_gender = _make_outfit(items=[
            {"title": "남성 셔츠", "gender": "male", "brand": "무신사 스탠다드", "tone_id": "summer_cool_soft"},
        ])

        result = apply_hard_filters(
            [good, bad_budget, bad_gender],
            user_gender="female",
            budget_max=100000,
            user_tpo_list=["office"],
            user_tone_id="summer_cool_soft",
            current_month=4,
        )
        assert len(result) == 1

    def test_empty_list(self):
        result = apply_hard_filters([])
        assert result == []

    def test_style_details_added(self):
        """통과한 코디에 style_details가 추가된다."""
        result = apply_hard_filters(
            [_make_outfit()],
            user_gender="female",
            budget_max=200000,
            user_tpo_list=["office"],
            user_tone_id="summer_cool_soft",
            current_month=4,
        )
        assert "style_details" in result[0]
