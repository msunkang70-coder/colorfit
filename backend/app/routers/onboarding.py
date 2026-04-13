"""
Onboarding API — POST /api/onboarding
온보딩 5 Step 결과를 수집하여 사용자 프로필을 생성한다.
MVP에서는 JSON 파일로 저장. DB 연동 시 SQLAlchemy로 전환 예정.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from fastapi import APIRouter

from app.schemas.onboarding import OnboardingRequest, OnboardingResponse

router = APIRouter(prefix="/api", tags=["onboarding"])

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_USERS_PATH = _DATA_DIR / "users.json"


def _load_users() -> list[dict]:
    """저장된 사용자 목록을 로드한다."""
    if _USERS_PATH.exists():
        with open(_USERS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_users(users: list[dict]) -> None:
    """사용자 목록을 파일에 저장한다."""
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(_USERS_PATH, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


@router.post("/onboarding", response_model=OnboardingResponse)
async def create_onboarding(body: OnboardingRequest) -> OnboardingResponse:
    """온보딩 결과를 저장하고 사용자 ID를 반환한다."""
    user_id = str(uuid.uuid4())

    user_data = {
        "id": user_id,
        "gender": body.gender,
        "tone_id": body.tone_id,
        "tpo_list": body.tpo_list,
        "style_moods": body.style_moods,
        "budget_min": body.budget_min,
        "budget_max": body.budget_max,
        "style_seed_choices": [
            {"round": c.round, "image_id": c.image_id}
            for c in body.style_seed_choices
        ],
    }

    users = _load_users()
    users.append(user_data)
    _save_users(users)

    return OnboardingResponse(user_id=user_id)


@router.get("/onboarding/summary")
async def get_onboarding_summary() -> dict:
    """온보딩 완료 사용자 요약."""
    users = _load_users()
    genders = {}
    tones = {}
    tpos = {}
    moods = {}
    for u in users:
        g = u.get("gender", "unknown")
        genders[g] = genders.get(g, 0) + 1
        t = u.get("tone_id", "unknown")
        tones[t] = tones.get(t, 0) + 1
        for tp in u.get("tpo_list", []):
            tpos[tp] = tpos.get(tp, 0) + 1
        for m in u.get("style_moods", []):
            moods[m] = moods.get(m, 0) + 1
    return {"total": len(users), "genders": genders, "tones": tones, "tpos": tpos, "moods": moods}
