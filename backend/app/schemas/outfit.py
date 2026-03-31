"""Pydantic 스키마 — 코디/피드 요청·응답 DTO."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ItemResponse(BaseModel):
    product_id: str
    category: str = ""
    name: str = ""
    brand: str = ""
    color_hex: str = ""
    tone_id: str = ""
    price: int = 0
    mall_name: str = ""
    mall_url: str = ""
    image_url: str = ""


class ScoresResponse(BaseModel):
    personal_color_fit: float = Field(alias="pcf")
    occasion_fit: float = Field(alias="of")
    color_harmony: float = Field(alias="ch")
    price_efficiency: float = Field(alias="pe")
    style_fit: float = Field(alias="sf")
    total: float = 0

    model_config = {"populate_by_name": True}


class OutfitResponse(BaseModel):
    outfit_id: str
    items: list[ItemResponse] = []
    scores: ScoresResponse | None = None
    reasons: list[str] = []
    tags: list[str] = []
    is_complete_outfit: bool = False
    total_price: int = 0


class FeedRequest(BaseModel):
    tone_id: str = ""
    tpo: list[str] = []
    gender: str = ""
    budget_min: float = 0
    budget_max: float = 300000
    page: int = 1
    page_size: int = 20


class FeedResponse(BaseModel):
    outfits: list[OutfitResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool
