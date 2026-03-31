"""리액션 API 테스트."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_REACTIONS_PATH = _DATA_DIR / "reactions.json"


@pytest.fixture(autouse=True)
def _clean_reactions_file():
    backup = None
    if _REACTIONS_PATH.exists():
        backup = _REACTIONS_PATH.read_text(encoding="utf-8")
    yield
    if backup is not None:
        _REACTIONS_PATH.write_text(backup, encoding="utf-8")
    elif _REACTIONS_PATH.exists():
        _REACTIONS_PATH.unlink()


class TestPostReaction:
    def test_save(self):
        body = {
            "user_id": "test-user-1",
            "outfit_id": "outfit-1",
            "reaction_type": "save",
        }
        res = client.post("/api/reaction", json=body)
        assert res.status_code == 200
        assert res.json()["status"] == "ok"

    def test_dislike(self):
        body = {
            "user_id": "test-user-1",
            "outfit_id": "outfit-2",
            "reaction_type": "dislike",
        }
        res = client.post("/api/reaction", json=body)
        assert res.status_code == 200

    def test_invalid_type(self):
        body = {
            "user_id": "test-user-1",
            "outfit_id": "outfit-1",
            "reaction_type": "love",
        }
        res = client.post("/api/reaction", json=body)
        assert res.status_code == 422

    def test_toggle_replaces_previous(self):
        body = {
            "user_id": "test-user-1",
            "outfit_id": "outfit-1",
            "reaction_type": "save",
        }
        client.post("/api/reaction", json=body)
        # Change to dislike
        body["reaction_type"] = "dislike"
        client.post("/api/reaction", json=body)

        import json
        reactions = json.loads(_REACTIONS_PATH.read_text(encoding="utf-8"))
        matching = [
            r for r in reactions
            if r["user_id"] == "test-user-1" and r["outfit_id"] == "outfit-1"
        ]
        assert len(matching) == 1
        assert matching[0]["reaction_type"] == "dislike"
