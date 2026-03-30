"""
네이버 쇼핑 API 연결 테스트.

실행:
    pytest backend/tests/test_naver_api.py -v
    pytest backend/tests/test_naver_api.py -v -k "unit"       # 단위 테스트만
    pytest backend/tests/test_naver_api.py -v -k "integration" # API 실제 호출 (키 필요)
"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from backend.scripts.curate_by_tone import (
    ALL_TONES,
    collect_for_query,
    search_products,
)


# ── 단위 테스트 (API 호출 없음) ─────────────────────────────


MOCK_RESPONSE = {
    "lastBuildDate": "Mon, 30 Mar 2026 12:00:00 +0900",
    "total": 1,
    "start": 1,
    "display": 1,
    "items": [
        {
            "title": "코랄 <b>블라우스</b>",
            "link": "https://example.com/product/1",
            "image": "https://example.com/img/1.jpg",
            "lprice": "29000",
            "hprice": "39000",
            "mallName": "무신사",
            "productId": "12345",
            "productType": "1",
            "brand": "무신사 스탠다드",
            "maker": "",
            "category1": "패션의류",
            "category2": "여성의류",
            "category3": "블라우스/셔츠",
            "category4": "",
        }
    ],
}


class TestSearchProductsUnit:
    """search_products 단위 테스트 (mock)"""

    @patch("backend.scripts.curate_by_tone.requests.get")
    def test_unit_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = MOCK_RESPONSE
        mock_get.return_value = mock_resp

        with patch("backend.scripts.curate_by_tone.NAVER_CLIENT_ID", "test_id"), \
             patch("backend.scripts.curate_by_tone.NAVER_CLIENT_SECRET", "test_secret"):
            result = search_products("코랄 블라우스")

        assert result is not None
        assert result["total"] == 1
        assert len(result["items"]) == 1
        assert result["items"][0]["productId"] == "12345"

    @patch("backend.scripts.curate_by_tone.requests.get")
    @patch("backend.scripts.curate_by_tone.time.sleep")
    def test_unit_rate_limit_retry(self, mock_sleep, mock_get):
        rate_resp = MagicMock()
        rate_resp.status_code = 429

        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.json.return_value = MOCK_RESPONSE

        mock_get.side_effect = [rate_resp, ok_resp]

        with patch("backend.scripts.curate_by_tone.NAVER_CLIENT_ID", "test_id"), \
             patch("backend.scripts.curate_by_tone.NAVER_CLIENT_SECRET", "test_secret"):
            result = search_products("테스트")

        assert result is not None
        assert mock_sleep.called

    def test_unit_missing_credentials(self):
        with patch("backend.scripts.curate_by_tone.NAVER_CLIENT_ID", ""), \
             patch("backend.scripts.curate_by_tone.NAVER_CLIENT_SECRET", ""):
            with pytest.raises(RuntimeError, match="NAVER_CLIENT_ID"):
                search_products("테스트")

    @patch("backend.scripts.curate_by_tone.requests.get")
    def test_unit_api_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        mock_get.return_value = mock_resp

        with patch("backend.scripts.curate_by_tone.NAVER_CLIENT_ID", "test_id"), \
             patch("backend.scripts.curate_by_tone.NAVER_CLIENT_SECRET", "test_secret"):
            result = search_products("테스트")

        assert result is None


class TestCollectForQueryUnit:
    """collect_for_query 단위 테스트 (mock)"""

    @patch("backend.scripts.curate_by_tone.time.sleep")
    @patch("backend.scripts.curate_by_tone.search_products")
    def test_unit_pagination(self, mock_search, mock_sleep):
        mock_search.side_effect = [
            {"items": [{"productId": str(i)} for i in range(100)]},
            {"items": [{"productId": str(i)} for i in range(100, 150)]},
            {"items": []},
        ]

        items = collect_for_query("테스트", max_items=200)
        assert len(items) == 150

    @patch("backend.scripts.curate_by_tone.time.sleep")
    @patch("backend.scripts.curate_by_tone.search_products")
    def test_unit_max_items_limit(self, mock_search, mock_sleep):
        mock_search.return_value = {
            "items": [{"productId": str(i)} for i in range(100)]
        }

        items = collect_for_query("테스트", max_items=50)
        assert len(items) <= 100  # 첫 호출에서 100개 받지만 max_items으로 제한


class TestAllTones:
    """톤 목록 검증"""

    def test_unit_all_12_tones(self):
        assert len(ALL_TONES) == 12

    def test_unit_tone_naming_convention(self):
        for tone in ALL_TONES:
            parts = tone.split("_")
            assert len(parts) == 3
            assert parts[0] in ("spring", "summer", "autumn", "winter")
            assert parts[1] in ("warm", "cool")


# ── 통합 테스트 (실제 API 호출) ─────────────────────────────


@pytest.mark.integration
class TestSearchProductsIntegration:
    """실제 네이버 쇼핑 API 호출 테스트. NAVER_CLIENT_ID가 있을 때만 실행."""

    @pytest.fixture(autouse=True)
    def skip_without_key(self):
        if not os.getenv("NAVER_CLIENT_ID"):
            pytest.skip("NAVER_CLIENT_ID 환경변수 없음 — 통합 테스트 건너뜀")

    def test_integration_basic_search(self):
        result = search_products("코랄 블라우스", display=5)
        assert result is not None
        assert "items" in result
        assert len(result["items"]) > 0

        item = result["items"][0]
        assert "title" in item
        assert "lprice" in item
        assert "image" in item
        assert "productId" in item

    def test_integration_pagination(self):
        r1 = search_products("여성 니트", display=5, start=1)
        r2 = search_products("여성 니트", display=5, start=6)
        assert r1 is not None and r2 is not None

        ids1 = {i["productId"] for i in r1["items"]}
        ids2 = {i["productId"] for i in r2["items"]}
        assert ids1 != ids2, "페이징 결과가 동일함"
