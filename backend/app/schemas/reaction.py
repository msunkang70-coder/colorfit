"""리액션 요청/응답 스키마."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ReactionRequest(BaseModel):
    user_id: str
    outfit_id: str
    reaction_type: str = Field(pattern=r"^(save|dislike)$")


class ReactionResponse(BaseModel):
    status: str = "ok"
