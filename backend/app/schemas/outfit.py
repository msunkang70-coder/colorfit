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
    style_tag: str = ""
    formality: float = 0


class ScoresResponse(BaseModel):
    tpo: float = Field(0, alias="tpo", description="TPO 적합도 0-100")
    fit: float = Field(0, alias="fit", description="체형/핏 적합도 0-100")
    color: float = Field(0, alias="color", description="컬러 조합 0-100")
    style: float = Field(0, alias="style", description="스타일 일관성 0-100")
    risk: float = Field(0, alias="risk", description="리스크 감점 -30~0")
    final: float = Field(0, alias="final", description="최종 점수 0-100")
    # 기존 호환 (프론트 깨짐 방지)
    pcf: float = 0
    of: float = 0
    ch: float = 0
    pe: float = 0
    sf: float = 0
    total: float = 0

    model_config = {"populate_by_name": True}


class ReasonResponse(BaseModel):
    """추천 사유 3파트."""
    core: str = ""
    risk_guard: str = ""
    situation: str = ""
    # 기존 호환
    evidence: str = ""


class OutfitResponse(BaseModel):
    outfit_id: str
    items: list[ItemResponse] = []
    scores: ScoresResponse | None = None
    reasons: ReasonResponse | None = None
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
