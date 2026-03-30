"""rebuild_from_tones.py 단위 테스트."""

import pytest

from backend.scripts.rebuild_from_tones import (
    NormalizedProduct,
    extract_brand,
    normalize_item,
    parse_price,
    strip_html,
)


class TestStripHtml:
    def test_basic_tags(self):
        assert strip_html("코랄 <b>블라우스</b>") == "코랄 블라우스"

    def test_multiple_tags(self):
        assert strip_html("<b>무신사</b> <i>스탠다드</i> 니트") == "무신사 스탠다드 니트"

    def test_no_tags(self):
        assert strip_html("일반 텍스트") == "일반 텍스트"

    def test_empty_string(self):
        assert strip_html("") == ""

    def test_extra_spaces(self):
        assert strip_html("  코랄   블라우스  ") == "코랄 블라우스"


class TestExtractBrand:
    def test_brand_from_api_field(self):
        assert extract_brand("니트", "무신사", "유니클로") == "유니클로"

    def test_brand_from_title(self):
        assert extract_brand("COS 캐시미어 니트", "어딘가") == "COS"

    def test_brand_from_mallname(self):
        assert extract_brand("그냥 니트", "유니클로") == "유니클로"

    def test_unknown_brand(self):
        assert extract_brand("니트", "알수없는몰") == "알수없는몰"

    def test_longer_brand_first(self):
        # "무신사 스탠다드 우먼" > "무신사 스탠다드"
        result = extract_brand("무신사 스탠다드 우먼 니트", "")
        assert result == "무신사 스탠다드 우먼"


class TestParsePrice:
    def test_lprice(self):
        assert parse_price("29000") == 29000

    def test_hprice_fallback(self):
        assert parse_price("", "39000") == 39000

    def test_both_empty(self):
        assert parse_price("", "") == 0

    def test_non_numeric(self):
        assert parse_price("abc") == 0


class TestNormalizeItem:
    def test_basic_normalization(self):
        raw = {
            "title": "코랄 <b>블라우스</b>",
            "link": "https://example.com/1",
            "image": "https://example.com/img/1.jpg",
            "lprice": "29000",
            "hprice": "39000",
            "mallName": "무신사",
            "productId": "12345",
            "brand": "무신사 스탠다드",
            "category1": "패션의류",
            "category2": "여성의류",
            "category3": "블라우스",
            "category4": "",
        }

        result = normalize_item(raw, "spring_warm_light")

        assert result.product_id == "12345"
        assert result.name == "코랄 블라우스"  # HTML 제거됨
        assert result.brand == "무신사 스탠다드"
        assert result.price == 29000
        assert result.mall_url == "https://example.com/1"
        assert result.source_tone == "spring_warm_light"
        assert result.category == ""  # Task 1.8에서 채움
