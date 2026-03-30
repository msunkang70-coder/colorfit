"""classifier.py 단위 테스트."""

import pytest

from backend.scripts.classifier import (
    classify_by_keyword,
    classify_product,
)


class TestClassifyByKeyword:
    def test_knit(self):
        r = classify_by_keyword("워셔블 캐시미어 V넥 니트")
        assert r is not None
        assert r["category"] == "니트"

    def test_blouse(self):
        r = classify_by_keyword("코랄 프릴블라우스 여성")
        assert r["category"] == "블라우스"
        assert r["gender"] == "female"

    def test_denim(self):
        r = classify_by_keyword("슬림핏 데님 팬츠")
        assert r["category"] == "청바지"
        assert r["silhouette"] == "slim"

    def test_blazer(self):
        r = classify_by_keyword("오버핏 블레이저 자켓")
        assert r["category"] == "자켓"
        assert r["silhouette"] == "oversized"
        assert r["formality"] == 4

    def test_dress(self):
        r = classify_by_keyword("플로럴 미니원피스")
        assert r["category"] == "원피스"

    def test_sneakers(self):
        r = classify_by_keyword("뉴발란스 러닝화 530")
        assert r["category"] == "스니커즈"
        assert r["formality"] == 2

    def test_male_keyword(self):
        r = classify_by_keyword("남성 슬림 셔츠")
        assert r["gender"] == "male"

    def test_no_match(self):
        r = classify_by_keyword("워셔블 캐시미어 V넥 풀오버")
        # "풀오버"는 니트 키워드에 포함되어 있음
        assert r is not None
        assert r["category"] == "니트"

    def test_truly_no_match(self):
        r = classify_by_keyword("일반 용품 잡화")
        assert r is None

    def test_tpo_workout(self):
        r = classify_by_keyword("여성 레깅스 요가")
        assert r["category"] == "레깅스"
        assert "workout" in r["tpo"]

    def test_tpo_formal(self):
        r = classify_by_keyword("여성 블라우스 오피스")
        assert "commute" in r["tpo"] or "interview" in r["tpo"]

    def test_cat_hint_used(self):
        r = classify_by_keyword("루즈핏 면 바지", cat_hint="치노")
        assert r is not None
        assert r["category"] == "치노"


class TestClassifyProduct:
    def test_keyword_method(self):
        r = classify_product("p1", "코랄 니트", use_llm=False)
        assert r["_method"] == "keyword"
        assert r["category"] == "니트"

    def test_fallback_no_llm(self):
        r = classify_product("p2", "알수없는 물건", use_llm=False)
        assert r["_method"] == "fallback"
        assert r["category"] == "unknown"

    def test_formality_range(self):
        r = classify_by_keyword("힐 하이힐 펌프스")
        assert r["formality"] == 5

        r2 = classify_by_keyword("레깅스 스포츠")
        assert r2["formality"] == 1
