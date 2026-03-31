"""Task 2.5 — SF 스코어링 테스트."""

import pytest
from app.services.scoring import (
    calculate_sf,
    _category_compat_score,
    _silhouette_score,
    _formality_score,
    _compat_key,
)


class TestHelpers:

    def test_compat_key_sorted(self):
        assert _compat_key("slacks", "blouse") == "blouse|slacks"
        assert _compat_key("blouse", "slacks") == "blouse|slacks"

    def test_compat_key_lowercase(self):
        assert _compat_key("BLOUSE", "Slacks") == "blouse|slacks"


class TestCategoryCompat:

    def test_blouse_slacks_high(self):
        """블라우스+슬랙스 → 90점."""
        score = _category_compat_score(["blouse", "slacks"])
        assert score == 90.0

    def test_hoodie_slacks_low(self):
        """후드+슬랙스 → 35점."""
        score = _category_compat_score(["hoodie", "slacks"])
        assert score == 35.0

    def test_unknown_combo_default(self):
        """미등록 조합 → 60점 기본값."""
        score = _category_compat_score(["unknown_cat1", "unknown_cat2"])
        assert score == 60.0

    def test_single_item(self):
        """단일 아이템 → 70점 중립."""
        score = _category_compat_score(["blouse"])
        assert score == 70.0

    def test_multi_items_average(self):
        """3개 아이템 → 모든 쌍 평균."""
        score = _category_compat_score(["blouse", "slacks", "loafer"])
        # blouse|slacks=90, blouse|loafer=90, loafer|slacks=92 → avg=90.67
        assert 90 <= score <= 91


class TestSilhouette:

    def test_y_line(self):
        """Y라인: oversized + slim → 95점."""
        score = _silhouette_score("oversized", "slim")
        assert score == 95.0

    def test_a_line(self):
        """A라인: fitted + wide → 95점."""
        score = _silhouette_score("fitted", "wide")
        assert score == 95.0

    def test_x_line(self):
        """X라인: crop + high_waist → 90점."""
        score = _silhouette_score("crop", "high_waist")
        assert score == 90.0

    def test_volume_overload(self):
        """볼륨 과다: oversized + wide → 60점."""
        score = _silhouette_score("oversized", "wide")
        assert score == 60.0

    def test_unknown_combo(self):
        """미등록 실루엣 → 65점."""
        score = _silhouette_score("unknown", "unknown")
        assert score == 65.0

    def test_missing_info(self):
        """정보 없음 → 70점."""
        score = _silhouette_score(None, None)
        assert score == 70.0


class TestFormality:

    def test_perfect_match(self):
        """포멀도 동일 → 100점."""
        score = _formality_score(["blouse", "slacks"])  # 둘 다 4
        assert score == 100.0

    def test_one_step_diff(self):
        """포멀도 1단계 차이 → ~80점."""
        score = _formality_score(["blouse", "knit"])  # 4, 3
        assert 75 <= score <= 85

    def test_hoodie_suit_big_diff(self):
        """후드+정장 → 큰 편차 → 낮은 점수."""
        score = _formality_score(["hoodie", "blazer"])  # 2, 5
        assert score < 50

    def test_single_item_perfect(self):
        """단일 아이템 → 100점."""
        score = _formality_score(["blouse"])
        assert score == 100.0


class TestCalculateSF:

    def test_blouse_slacks_loafer_high(self):
        """블라우스+슬랙스+로퍼 (fitted+slim) → 높은 SF."""
        score = calculate_sf(
            categories=["blouse", "slacks", "loafer"],
            top_silhouette="fitted",
            bottom_silhouette="slim",
        )
        assert score >= 75

    def test_hoodie_slacks_heels_low(self):
        """후드+슬랙스+하이힐 → 낮은 SF (카테고리 부조화 + 포멀도 불일치)."""
        score = calculate_sf(
            categories=["hoodie", "slacks", "heels"],
        )
        assert score < 60

    def test_cutoff_boundary_55(self):
        """55점 컷오프 경계 테스트."""
        # 좋은 조합은 55점 이상
        good = calculate_sf(
            categories=["knit", "jeans", "sneakers"],
            top_silhouette="regular",
            bottom_silhouette="straight",
        )
        assert good >= 55

    def test_empty_categories(self):
        """빈 카테고리 → 50점."""
        score = calculate_sf(categories=[])
        assert score == 50.0

    def test_no_silhouette_info(self):
        """실루엣 정보 없이도 동작."""
        score = calculate_sf(categories=["blouse", "skirt"])
        assert 0 <= score <= 100

    def test_score_range(self):
        """점수는 항상 0~100."""
        cases = [
            (["hoodie", "blazer", "heels"], "oversized", "wide"),
            (["blouse", "slacks", "loafer"], "fitted", "slim"),
            (["tshirt", "jeans"], None, None),
        ]
        for cats, top, bot in cases:
            score = calculate_sf(cats, top, bot)
            assert 0 <= score <= 100, f"cats={cats}, score={score}"
