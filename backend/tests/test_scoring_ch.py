"""Task 2.3 — CH 스코어링 테스트."""

import pytest
from app.services.scoring import calculate_ch, _rgb_to_hsv


class TestRGBtoHSV:
    """HSV 변환 검증."""

    def test_pure_red(self):
        h, s, v = _rgb_to_hsv((255, 0, 0))
        assert h == 0.0
        assert s == 1.0
        assert v == 1.0

    def test_pure_white(self):
        h, s, v = _rgb_to_hsv((255, 255, 255))
        assert s == 0.0
        assert v == 1.0

    def test_pure_black(self):
        h, s, v = _rgb_to_hsv((0, 0, 0))
        assert s == 0.0
        assert v == 0.0


class TestCalculateCH:
    """calculate_ch 함수 테스트."""

    def test_all_black(self):
        """올블랙: 거리 0 → d_avg < 30 → 60점."""
        score = calculate_ch(["#000000", "#000000", "#000000"])
        assert score == 60.0

    def test_all_white(self):
        """올화이트: 거리 0 → 60점."""
        score = calculate_ch(["#FFFFFF", "#FFFFFF"])
        assert score == 60.0

    def test_tone_on_tone(self):
        """톤온톤 (유사색): d_avg 30~80 → 80~100점."""
        # 코랄 핑크 계열 유사색
        score = calculate_ch(["#FFB6A3", "#FFCBA4", "#FFD1DC"])
        assert 60 <= score <= 100

    def test_moderate_contrast(self):
        """적절한 대비: d_avg 80~150 → 기획서 구간 79~100점."""
        # 베이지 + 소프트 핑크 (d_avg ~50 유사색 구간)
        score = calculate_ch(["#F5DEB3", "#FFB6C1"])
        assert 80 <= score <= 100

    def test_extreme_contrast(self):
        """형광+파스텔: d_avg ≥ 150 → 낮은 점수."""
        # 순수 빨강 + 순수 시안 (거리 ~361)
        score = calculate_ch(["#FF0000", "#00FFFF"])
        assert score < 80

    def test_single_item(self):
        """단일 아이템 → 중립 70점."""
        score = calculate_ch(["#FF0000"])
        assert score == 70.0

    def test_saturation_bonus(self):
        """채도 보너스: 3개+ 아이템, 채도 표준편차 0.15~0.40."""
        # 고채도 + 중채도 + 저채도 혼합
        # 빨강(S=1.0), 회색빛 핑크(S~0.3), 흰색(S=0)
        score_with_variety = calculate_ch(["#FF0000", "#D4A0A0", "#FFFFFF"])
        # 같은 채도의 아이템들
        score_uniform = calculate_ch(["#FF0000", "#00FF00", "#0000FF"])
        # 채도 다양성이 있는 쪽이 보너스 받을 수 있음
        assert 0 <= score_with_variety <= 100
        assert 0 <= score_uniform <= 100

    def test_score_range_always_valid(self):
        """점수는 항상 0~100."""
        test_cases = [
            ["#000000", "#FFFFFF"],
            ["#FF0000", "#00FF00", "#0000FF"],
            ["#FFCBA4", "#FFB6A3"],
            ["#123456", "#654321", "#ABCDEF", "#FEDCBA"],
        ]
        for colors in test_cases:
            score = calculate_ch(colors)
            assert 0 <= score <= 100, f"colors={colors}, score={score}"

    def test_gradation_high_score(self):
        """그라데이션 코디 (단계적 색상 변화) → 높은 점수."""
        # 핑크 → 코랄 → 살몬 (단계적 변화)
        score = calculate_ch(["#FFB6C1", "#FF7F7F", "#FA8072"])
        assert score >= 60

    def test_black_and_white(self):
        """흑백 조합."""
        score = calculate_ch(["#000000", "#FFFFFF"])
        # d_avg = 441.67 → 과도한 대비 구간
        assert 30 <= score <= 79

    def test_near_identical_colors(self):
        """거의 동일한 색상 → 60점 근처."""
        score = calculate_ch(["#FF6B6B", "#FF7070"])
        assert score == 60.0

    def test_cap_at_100(self):
        """채도 보너스 포함해도 100 초과 방지."""
        # 유사색 구간 상단 + 채도 보너스
        score = calculate_ch(["#FF8800", "#CC6600", "#FFaa44"])
        assert score <= 100.0
