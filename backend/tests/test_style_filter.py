"""Task 2.7 — StyleFilter 테스트."""

import pytest
from app.services.style_filter import detect_category, filter_outfit, SF_CUTOFF


class TestDetectCategory:

    def test_keyword_match_blouse(self):
        result = detect_category("여성 프릴블라우스 아이보리")
        assert result["category"] == "블라우스"

    def test_keyword_match_hoodie(self):
        result = detect_category("오버핏 후드티 블랙")
        assert result["category"] == "후드"

    def test_keyword_match_with_category3(self):
        result = detect_category("남성 기본 상의", "니트/스웨터")
        assert result["category"] == "니트"

    def test_unknown_fallback(self):
        result = detect_category("정체불명의 상품명 XYZ123")
        assert result["category"] == "unknown"
        assert result["silhouette"] == "regular"
        assert result["formality"] == 3

    def test_silhouette_detected(self):
        result = detect_category("오버사이즈 니트 베이지")
        assert result["silhouette"] == "oversized"


class TestFilterOutfit:

    def test_good_outfit_passes(self):
        """블라우스+슬랙스+로퍼 → 통과."""
        items = [
            {"title": "여성 블라우스 라벤더"},
            {"title": "슬랙스 아이보리"},
            {"title": "클래식 로퍼 브라운"},
        ]
        passed, score, details = filter_outfit(items)
        assert passed is True
        assert score >= SF_CUTOFF
        assert len(details["categories_detected"]) == 3

    def test_bad_outfit_fails(self):
        """후드+슬랙스+하이힐 → 탈락 (카테고리 부조화 + 포멀도 불일치)."""
        items = [
            {"title": "오버핏 후드티 블랙"},
            {"title": "정장 슬랙스 네이비"},
            {"title": "하이힐 펌프스 레드"},
        ]
        passed, score, details = filter_outfit(items)
        assert passed is False
        assert score < SF_CUTOFF

    def test_casual_outfit_passes(self):
        """니트+청바지+스니커즈 → 통과."""
        items = [
            {"title": "캐시미어 니트 베이지"},
            {"title": "데님 청바지 인디고"},
            {"title": "캔버스화 스니커즈 화이트"},
        ]
        passed, score, details = filter_outfit(items)
        assert passed is True

    def test_onepiece_combo_passes(self):
        """원피스+가디건+로퍼 → 통과."""
        items = [
            {"title": "롱원피스 플로럴"},
            {"title": "여성 가디건 크림"},
            {"title": "클래식 로퍼"},
        ]
        passed, score, details = filter_outfit(items)
        assert passed is True

    def test_score_boundary_55(self):
        """55점 기준 경계값 확인."""
        assert SF_CUTOFF == 55.0

    def test_details_contain_categories(self):
        """details에 감지된 카테고리 포함."""
        items = [
            {"title": "셔츠 스트라이프"},
            {"title": "슬랙스 차콜"},
        ]
        _, _, details = filter_outfit(items)
        assert "categories_detected" in details
        assert "shirt" in details["categories_detected"]
        assert "slacks" in details["categories_detected"]

    def test_empty_items(self):
        """빈 아이템 → 기본 처리."""
        passed, score, details = filter_outfit([])
        assert isinstance(passed, bool)
        assert isinstance(score, float)

    def test_silhouette_detection(self):
        """실루엣이 details에 포함."""
        items = [
            {"title": "오버사이즈 니트"},
            {"title": "슬림핏 청바지"},
        ]
        _, _, details = filter_outfit(items)
        assert details["top_silhouette"] == "oversized"
        assert details["bottom_silhouette"] == "slim"
