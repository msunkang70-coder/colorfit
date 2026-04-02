"""Task 2.11 — Feed/Outfit API 엔드포인트 테스트."""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _mock_outfits():
    """테스트용 코디 데이터."""
    return [
        {
            "outfit_id": "test_o1",
            "items": [
                {"product_id": "p1", "title": "블라우스 아이보리", "brand": "무신사 스탠다드",
                 "gender": "female", "tone_id": "summer_cool_soft", "color_hex": "#B0A6C6",
                 "price": 32000, "category": "blouse", "mall_name": "무신사",
                 "mall_url": "https://example.com", "image_url": "https://img.example.com/1.jpg"},
                {"product_id": "p2", "title": "슬랙스 차콜", "brand": "유니클로",
                 "gender": "unisex", "tone_id": "summer_cool_soft", "color_hex": "#F5F0E8",
                 "price": 45000, "category": "slacks", "mall_name": "유니클로",
                 "mall_url": "https://example.com", "image_url": "https://img.example.com/2.jpg"},
            ],
            "total_price": 77000,
            "designed_tpo": ["commute", "office"],
            "tags": ["office", "spring"],
            "is_complete_outfit": False,
            "llm_quality_score": 4,
        },
        {
            "outfit_id": "test_o2",
            "items": [
                {"product_id": "p3", "title": "니트 베이지", "brand": "COS",
                 "gender": "female", "tone_id": "autumn_warm_mute", "color_hex": "#D4A574",
                 "price": 55000, "category": "knit", "mall_name": "COS",
                 "mall_url": "https://example.com", "image_url": "https://img.example.com/3.jpg"},
                {"product_id": "p4", "title": "청바지 인디고", "brand": "무신사 스탠다드",
                 "gender": "unisex", "tone_id": "autumn_warm_mute", "color_hex": "#3B5998",
                 "price": 39000, "category": "jeans", "mall_name": "무신사",
                 "mall_url": "https://example.com", "image_url": "https://img.example.com/4.jpg"},
            ],
            "total_price": 94000,
            "designed_tpo": ["casual", "weekend"],
            "tags": ["casual", "autumn"],
            "is_complete_outfit": False,
            "llm_quality_score": 4,
        },
    ]


@pytest.fixture(autouse=True)
def mock_outfit_data():
    with patch("app.routers.feed._load_outfits_from_json", return_value=_mock_outfits()):
        with patch("app.routers.outfit._load_outfits_map",
                    return_value={o["outfit_id"]: o for o in _mock_outfits()}):
            yield


class TestFeedEndpoint:

    def test_get_feed_basic(self):
        resp = client.get("/api/feed?tone_id=summer_cool_soft&gender=female&budget_max=200000")
        assert resp.status_code == 200
        data = resp.json()
        assert "outfits" in data
        assert "total_count" in data
        assert "page" in data
        assert "has_next" in data

    def test_feed_returns_scores(self):
        resp = client.get("/api/feed?tone_id=summer_cool_soft")
        data = resp.json()
        if data["outfits"]:
            outfit = data["outfits"][0]
            assert outfit["scores"] is not None
            scores = outfit["scores"]
            assert "personal_color_fit" in scores or "pcf" in scores

    def test_feed_returns_reasons(self):
        resp = client.get("/api/feed?tone_id=summer_cool_soft&tpo=office")
        data = resp.json()
        if data["outfits"]:
            reasons = data["outfits"][0]["reasons"]
            assert reasons is not None
            assert "core" in reasons
            assert "evidence" in reasons
            assert "risk_guard" in reasons

    def test_feed_pagination(self):
        resp = client.get("/api/feed?page=1&page_size=1")
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 1
        assert len(data["outfits"]) <= 1

    def test_feed_tpo_filter(self):
        resp = client.get("/api/feed?tpo=office&tone_id=summer_cool_soft&gender=female&budget_max=200000")
        data = resp.json()
        assert resp.status_code == 200

    def test_feed_empty_params(self):
        resp = client.get("/api/feed")
        assert resp.status_code == 200
        data = resp.json()
        assert "outfits" in data


class TestOutfitEndpoint:

    def test_get_outfit_found(self):
        resp = client.get("/api/outfit/test_o1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["outfit_id"] == "test_o1"
        assert len(data["items"]) == 2

    def test_get_outfit_not_found(self):
        resp = client.get("/api/outfit/nonexistent")
        assert resp.status_code == 404

    def test_outfit_items_fields(self):
        resp = client.get("/api/outfit/test_o1")
        data = resp.json()
        item = data["items"][0]
        assert "product_id" in item
        assert "name" in item
        assert "brand" in item
        assert "color_hex" in item
        assert "price" in item


class TestHealthCheck:

    def test_health(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
