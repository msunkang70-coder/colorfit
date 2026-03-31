"""온보딩 요청/응답 스키마."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class StyleSeedChoice(BaseModel):
    round: int = Field(ge=1, le=4)
    image_id: str


class OnboardingRequest(BaseModel):
    gender: str = Field(pattern=r"^(female|male)$")
    tone_id: str = Field(
        pattern=r"^(spring_warm|summer_cool|autumn_warm|winter_cool)_(light|bright|mute|deep|soft)$"
    )
    tpo_list: list[str] = Field(min_length=1, max_length=3)
    style_moods: list[str] = Field(default=[], max_length=5)
    budget_min: int = Field(ge=0)
    budget_max: int = Field(gt=0)
    style_seed_choices: list[StyleSeedChoice] = Field(default=[])


class OnboardingResponse(BaseModel):
    user_id: str
    status: str = "ok"
