"""Task 2.1 — PCF 스코어링 테스트."""

import pytest
from app.services.scoring import (
    calculate_pcf,
    TONE_COMPAT,
    TONE_IDS,
    _hex_to_rgb,
    _rgb_distance,
)


class TestToneCompat:
    """톤 호환성 매트릭스 검증."""

    def test_self_is_100(self):
        """동일 톤 → 100점."""
        for tone in TONE_IDS:
            assert TONE_COMPAT[tone][tone] == 100

    def test_same_season_85_to_95(self):
        """같은 시즌 내 호환 톤 → 85~95점."""
        spring = ["spring_warm_light", "spring_warm_bright", "spring_warm_mute"]
        for u in spring:
            for i in spring:
                if u != i:
                    score = TONE_COMPAT[u][i]
                    assert 85 <= score <= 95, f"{u} → {i} = {score}"

    def test_same_temp_diff_season_60_to_75(self):
        """같은 온도, 다른 시즌 → 60~75점."""
        # 봄(웜) ↔ 가을(웜)
        score = TONE_COMPAT["spring_warm_light"]["autumn_warm_mute"]
        assert 60 <= score <= 75, f"spring_warm_light → autumn_warm_mute = {score}"

    def test_opposite_temp_40_to_55(self):
        """반대 온도 (웜↔쿨) → 40~55점."""
        score = TONE_COMPAT["spring_warm_light"]["winter_cool_deep"]
        assert 40 <= score <= 55, f"spring_warm_light → winter_cool_deep = {score}"

    def test_symmetry(self):
        """매트릭스 대칭성 검증."""
        for u in TONE_IDS:
            for i in TONE_IDS:
                assert TONE_COMPAT[u][i] == TONE_COMPAT[i][u], \
                    f"비대칭: {u}→{i}={TONE_COMPAT[u][i]}, {i}→{u}={TONE_COMPAT[i][u]}"

    def test_all_144_combinations_exist(self):
        """12×12=144 조합 모두 존재."""
        assert len(TONE_COMPAT) == 12
        for tone in TONE_IDS:
            assert len(TONE_COMPAT[tone]) == 12


class TestHelpers:
    """헬퍼 함수 테스트."""

    def test_hex_to_rgb(self):
        assert _hex_to_rgb("#FF0000") == (255, 0, 0)
        assert _hex_to_rgb("#00FF00") == (0, 255, 0)
        assert _hex_to_rgb("000000") == (0, 0, 0)

    def test_rgb_distance_zero(self):
        assert _rgb_distance((0, 0, 0), (0, 0, 0)) == 0.0

    def test_rgb_distance_max(self):
        d = _rgb_distance((0, 0, 0), (255, 255, 255))
        assert abs(d - 441.67) < 0.01


class TestCalculatePCF:
    """calculate_pcf 함수 테스트."""

    def test_same_tone_returns_100(self):
        """동일 톤 아이템 → 100점."""
        score = calculate_pcf(
            item_tone_ids=["spring_warm_light", "spring_warm_light"],
            item_hex_colors=["#FFCBA4", "#FFB6A3"],
            user_tone_id="spring_warm_light",
        )
        assert score == 100.0

    def test_compatible_tone_high_score(self):
        """같은 시즌 호환 톤 → 85~95점."""
        score = calculate_pcf(
            item_tone_ids=["spring_warm_bright", "spring_warm_mute"],
            item_hex_colors=["#FFD700", "#F0E68C"],
            user_tone_id="spring_warm_light",
        )
        assert 85 <= score <= 95

    def test_opposite_season_low_score(self):
        """반대 시즌 톤 → 낮은 점수 (RGB 거리 또는 톤 매칭)."""
        score = calculate_pcf(
            item_tone_ids=["winter_cool_deep", "winter_cool_deep"],
            item_hex_colors=["#000080", "#191970"],
            user_tone_id="spring_warm_light",
        )
        assert score < 70

    def test_no_tone_id_uses_color_distance(self):
        """톤 ID 없을 때 RGB 거리 기반 점수."""
        # 봄웜라이트 팔레트의 피치색(#FFCBA4)과 매우 가까운 색
        score = calculate_pcf(
            item_tone_ids=[None],
            item_hex_colors=["#FFCBA4"],
            user_tone_id="spring_warm_light",
        )
        # 팔레트에 정확히 있는 색 → 거리 0 → 100점
        assert score == 100.0

    def test_no_tone_id_distant_color(self):
        """톤 ID 없고 먼 색상 → 낮은 점수."""
        score = calculate_pcf(
            item_tone_ids=[None],
            item_hex_colors=["#000000"],  # 검정 — 봄웜라이트와 거리 멀음
            user_tone_id="spring_warm_light",
        )
        assert score < 50

    def test_empty_items_returns_zero(self):
        """빈 아이템 리스트 → 0점."""
        score = calculate_pcf(
            item_tone_ids=[],
            item_hex_colors=[],
            user_tone_id="spring_warm_light",
        )
        assert score == 0.0

    def test_mixed_tones_average(self):
        """혼합 톤 아이템 → 평균 점수."""
        score = calculate_pcf(
            item_tone_ids=["spring_warm_light", "winter_cool_deep"],
            item_hex_colors=["#FFCBA4", "#000080"],
            user_tone_id="spring_warm_light",
        )
        # 첫 아이템 100, 두번째 낮음 → 평균은 중간 범위
        assert 40 < score < 80

    def test_score_range_0_to_100(self):
        """점수는 항상 0~100 범위."""
        for user_tone in ["spring_warm_light", "winter_cool_deep", "autumn_warm_mute"]:
            score = calculate_pcf(
                item_tone_ids=["summer_cool_soft"],
                item_hex_colors=["#87CEEB"],
                user_tone_id=user_tone,
            )
            assert 0 <= score <= 100

    def test_boundary_white(self):
        """경계값: 순백색."""
        score = calculate_pcf(
            item_tone_ids=[None],
            item_hex_colors=["#FFFFFF"],
            user_tone_id="spring_warm_light",
        )
        assert 0 <= score <= 100

    def test_boundary_black(self):
        """경계값: 순흑색."""
        score = calculate_pcf(
            item_tone_ids=[None],
            item_hex_colors=["#000000"],
            user_tone_id="winter_cool_deep",
        )
        assert 0 <= score <= 100
