"""Task 2.2 — OF 스코어링 테스트."""

import pytest
from app.services.scoring import calculate_of, TPO_SYNONYMS


class TestTPOSynonyms:
    """동의어 매핑 검증."""

    def test_commute_office_bidirectional(self):
        assert "office" in TPO_SYNONYMS["commute"]
        assert "commute" in TPO_SYNONYMS["office"]

    def test_weekend_casual_daily_group(self):
        for tpo in ["weekend", "casual", "daily"]:
            assert TPO_SYNONYMS[tpo] == {"casual", "weekend", "daily"}

    def test_interview_includes_office(self):
        assert "office" in TPO_SYNONYMS["interview"]

    def test_workout_isolated(self):
        assert TPO_SYNONYMS["workout"] == {"workout"}


class TestCalculateOF:
    """calculate_of 함수 테스트."""

    def test_exact_match_single(self):
        """직접 매칭 → 100점."""
        score = calculate_of(
            outfit_tags=["office"],
            user_tpo_list=["office"],
        )
        assert score == 100.0

    def test_exact_match_multiple(self):
        """정확 매칭 2개 이상 → 80+ 점."""
        score = calculate_of(
            outfit_tags=["office", "commute"],
            user_tpo_list=["office", "commute"],
        )
        # match_count=2, total_tags=2 → 80 + (2/2)*20 = 100
        assert score == 100.0

    def test_synonym_match(self):
        """동의어 매칭: commute로 설정했지만 outfit에 office → 85점."""
        score = calculate_of(
            outfit_tags=["office"],
            user_tpo_list=["commute"],
        )
        assert score == 85.0

    def test_synonym_casual_weekend(self):
        """동의어: casual → {casual, weekend, daily} 확장 → 85점."""
        score = calculate_of(
            outfit_tags=["weekend", "daily"],
            user_tpo_list=["casual"],
        )
        assert score == 85.0

    def test_no_match(self):
        """미매칭 → 30점 하한."""
        score = calculate_of(
            outfit_tags=["workout"],
            user_tpo_list=["office"],
        )
        assert score == 30.0

    def test_partial_match(self):
        """직접 매칭 있으면 → 100점 (outfit에 office 포함)."""
        score = calculate_of(
            outfit_tags=["office", "interview", "formal"],
            user_tpo_list=["office"],
        )
        assert score == 100.0

    def test_empty_outfit_tags(self):
        """빈 태그 → 50점 (기본값)."""
        assert calculate_of([], ["office"]) == 50.0

    def test_empty_user_tpo(self):
        """빈 사용자 TPO → 50점 (기본값)."""
        assert calculate_of(["office"], []) == 50.0

    def test_score_range(self):
        """점수는 항상 30~100."""
        test_cases = [
            (["office"], ["workout"]),
            (["casual", "daily", "weekend"], ["casual"]),
            (["event"], ["party"]),
            (["campus"], ["campus", "casual"]),
        ]
        for tags, tpos in test_cases:
            score = calculate_of(tags, tpos)
            assert 30 <= score <= 100, f"tags={tags}, tpos={tpos}, score={score}"

    def test_case_insensitive(self):
        """대소문자 무시."""
        score = calculate_of(
            outfit_tags=["Office"],
            user_tpo_list=["OFFICE"],
        )
        assert score >= 60

    def test_unknown_tpo_passthrough(self):
        """알 수 없는 TPO는 자기 자신만으로 매칭."""
        score = calculate_of(
            outfit_tags=["travel"],
            user_tpo_list=["travel"],
        )
        # travel은 synonyms에 없지만, {travel}로 처리 → match_count=1
        assert score >= 60

    def test_multi_user_tpo_expansion(self):
        """사용자 TPO 여러 개 → 동의어 확장 매칭 → 85점."""
        score = calculate_of(
            outfit_tags=["office", "casual"],
            user_tpo_list=["commute", "weekend"],
        )
        # commute → {office, commute}, weekend → {casual, weekend, daily}
        # outfit에 office, casual이 expanded에 포함 → 동의어 매칭
        assert score == 85.0

    def test_cap_at_100(self):
        """점수 100 초과 방지."""
        score = calculate_of(
            outfit_tags=["casual", "weekend", "daily"],
            user_tpo_list=["casual", "weekend", "daily"],
        )
        assert score <= 100.0
