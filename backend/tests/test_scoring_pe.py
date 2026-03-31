"""Task 2.4 — PE 스코어링 테스트."""

import pytest
from app.services.scoring import calculate_pe


class TestCalculatePE:
    """calculate_pe 함수 테스트."""

    # ── Case 1: 예산 범위 내 ──

    def test_exact_center(self):
        """예산 정중앙 → 100점."""
        score = calculate_pe(75000, 50000, 100000)
        assert score == 100.0

    def test_within_range_near_max(self):
        """범위 내 상한 근처 → 70+ 점."""
        score = calculate_pe(95000, 50000, 100000)
        assert 70 <= score <= 100

    def test_within_range_near_min(self):
        """범위 내 하한 근처 → 70+ 점."""
        score = calculate_pe(55000, 50000, 100000)
        assert 70 <= score <= 100

    def test_exact_max(self):
        """상한 정확히 → 범위 내."""
        score = calculate_pe(100000, 50000, 100000)
        assert 70 <= score <= 100

    def test_exact_min(self):
        """하한 정확히 → 범위 내."""
        score = calculate_pe(50000, 50000, 100000)
        assert 70 <= score <= 100

    # ── Case 2: 예산 초과 ──

    def test_over_10_percent(self):
        """10% 초과 → ~60점."""
        score = calculate_pe(110000, 50000, 100000)
        assert 55 <= score <= 65

    def test_over_50_percent(self):
        """50% 초과 → ~20점."""
        score = calculate_pe(150000, 50000, 100000)
        assert 15 <= score <= 25

    def test_over_70_percent(self):
        """70%+ 초과 → 0점."""
        score = calculate_pe(170000, 50000, 100000)
        assert score == 0.0

    def test_extreme_over(self):
        """극단적 초과 → 0점."""
        score = calculate_pe(500000, 50000, 100000)
        assert score == 0.0

    # ── Case 3: 예산 미만 ──

    def test_slightly_under(self):
        """약간 미만 → 높은 점수."""
        score = calculate_pe(45000, 50000, 100000)
        assert 70 <= score <= 80

    def test_half_of_min(self):
        """최소의 절반 → 감점되지만 40점 이상."""
        score = calculate_pe(25000, 50000, 100000)
        assert 40 <= score <= 50

    def test_extreme_low(self):
        """극단적 저가 → 최저 40점."""
        score = calculate_pe(1000, 50000, 100000)
        assert score == 40.0

    def test_free(self):
        """무료(0원) → 최저 40점."""
        score = calculate_pe(0, 50000, 100000)
        assert score == 40.0

    # ── 경계값 + 범위 검증 ──

    def test_score_always_0_to_100(self):
        """점수 항상 0~100."""
        cases = [
            (75000, 50000, 100000),
            (200000, 50000, 100000),
            (1000, 50000, 100000),
            (30000, 30000, 30000),
        ]
        for price, bmin, bmax in cases:
            score = calculate_pe(price, bmin, bmax)
            assert 0 <= score <= 100, f"price={price}, range={bmin}~{bmax}, score={score}"

    def test_same_min_max(self):
        """최소 == 최대 → 정확히 맞으면 100점."""
        score = calculate_pe(50000, 50000, 50000)
        assert score == 100.0

    def test_budget_min_zero(self):
        """최소 예산 0원 → 범위 내면 정상 동작."""
        score = calculate_pe(50000, 0, 100000)
        assert 70 <= score <= 100
