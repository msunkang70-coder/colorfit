"""온보딩 API 테스트."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_USERS_PATH = _DATA_DIR / "users.json"


@pytest.fixture(autouse=True)
def _clean_users_file():
    """테스트 전후로 users.json을 정리한다."""
    backup = None
    if _USERS_PATH.exists():
        backup = _USERS_PATH.read_text(encoding="utf-8")

    yield

    if backup is not None:
        _USERS_PATH.write_text(backup, encoding="utf-8")
    elif _USERS_PATH.exists():
        _USERS_PATH.unlink()


class TestPostOnboarding:
    def test_success_minimal(self):
        body = {
            "gender": "female",
            "tone_id": "spring_warm_light",
            "tpo_list": ["commute"],
            "style_moods": [],
            "budget_min": 30000,
            "budget_max": 100000,
            "style_seed_choices": [],
        }
        res = client.post("/api/onboarding", json=body)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert "user_id" in data

    def test_success_full(self):
        body = {
            "gender": "male",
            "tone_id": "winter_cool_deep",
            "tpo_list": ["commute", "date", "weekend"],
            "style_moods": ["minimal", "street"],
            "budget_min": 50000,
            "budget_max": 150000,
            "style_seed_choices": [
                {"round": 1, "image_id": "r1-2"},
                {"round": 2, "image_id": "r2-4"},
            ],
        }
        res = client.post("/api/onboarding", json=body)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"

        # Verify saved to file
        users = json.loads(_USERS_PATH.read_text(encoding="utf-8"))
        saved = [u for u in users if u["id"] == data["user_id"]]
        assert len(saved) == 1
        assert saved[0]["gender"] == "male"
        assert saved[0]["tpo_list"] == ["commute", "date", "weekend"]

    def test_invalid_gender(self):
        body = {
            "gender": "other",
            "tone_id": "spring_warm_light",
            "tpo_list": ["commute"],
            "budget_min": 0,
            "budget_max": 100000,
        }
        res = client.post("/api/onboarding", json=body)
        assert res.status_code == 422

    def test_invalid_tone_id(self):
        body = {
            "gender": "female",
            "tone_id": "invalid_tone",
            "tpo_list": ["commute"],
            "budget_min": 0,
            "budget_max": 100000,
        }
        res = client.post("/api/onboarding", json=body)
        assert res.status_code == 422

    def test_empty_tpo_list(self):
        body = {
            "gender": "female",
            "tone_id": "spring_warm_light",
            "tpo_list": [],
            "budget_min": 0,
            "budget_max": 100000,
        }
        res = client.post("/api/onboarding", json=body)
        assert res.status_code == 422

    def test_tpo_list_exceeds_max(self):
        body = {
            "gender": "female",
            "tone_id": "spring_warm_light",
            "tpo_list": ["commute", "date", "weekend", "campus"],
            "budget_min": 0,
            "budget_max": 100000,
        }
        res = client.post("/api/onboarding", json=body)
        assert res.status_code == 422
