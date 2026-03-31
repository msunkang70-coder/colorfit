"""
Reaction API — POST /api/reaction
코디에 대한 save/dislike 반응을 저장한다.
MVP에서는 JSON 파일로 저장. DB 연동 시 SQLAlchemy로 전환 예정.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter

from app.schemas.reaction import ReactionRequest, ReactionResponse

router = APIRouter(prefix="/api", tags=["reaction"])

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_REACTIONS_PATH = _DATA_DIR / "reactions.json"


def _load_reactions() -> list[dict]:
    if _REACTIONS_PATH.exists():
        with open(_REACTIONS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_reactions(reactions: list[dict]) -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(_REACTIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(reactions, f, ensure_ascii=False, indent=2)


@router.post("/reaction", response_model=ReactionResponse)
async def create_reaction(body: ReactionRequest) -> ReactionResponse:
    """save/dislike 반응을 저장한다."""
    reactions = _load_reactions()

    # 동일 user+outfit의 기존 반응 제거 (토글 지원)
    reactions = [
        r
        for r in reactions
        if not (r["user_id"] == body.user_id and r["outfit_id"] == body.outfit_id)
    ]

    reactions.append({
        "user_id": body.user_id,
        "outfit_id": body.outfit_id,
        "reaction_type": body.reaction_type,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    _save_reactions(reactions)
    return ReactionResponse()
