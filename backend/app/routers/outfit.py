"""
Outfit API — GET /api/outfit/{id}
단일 코디 상세 조회.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.schemas.outfit import OutfitResponse, ScoresResponse, ItemResponse

router = APIRouter(prefix="/api", tags=["outfit"])

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"

_outfits_cache: dict[str, dict] | None = None


def _load_outfits_map() -> dict[str, dict]:
    """코디 맵 로드 (outfit_id → outfit dict). 캐싱."""
    global _outfits_cache
    if _outfits_cache is not None:
        return _outfits_cache

    path = _DATA_DIR / "outfits_evaluated.json"
    if not path.exists():
        path = _DATA_DIR / "outfits.json"
    if not path.exists():
        _outfits_cache = {}
        return _outfits_cache

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    _outfits_cache = {}
    for o in data:
        oid = o.get("outfit_id", o.get("id", ""))
        if oid:
            _outfits_cache[oid] = o

    return _outfits_cache


@router.get("/outfit/{outfit_id}", response_model=OutfitResponse)
async def get_outfit(outfit_id: str) -> OutfitResponse:
    """단일 코디 상세 조회."""
    outfits = _load_outfits_map()
    outfit = outfits.get(outfit_id)
    if not outfit:
        raise HTTPException(status_code=404, detail="코디를 찾을 수 없습니다")

    items = [
        ItemResponse(
            product_id=it.get("product_id", it.get("id", "")),
            category=it.get("category", ""),
            name=it.get("name", it.get("title", "")),
            brand=it.get("brand", it.get("mall_name", "")),
            color_hex=it.get("color_hex", ""),
            tone_id=it.get("tone_id", ""),
            price=it.get("price", 0),
            mall_name=it.get("mall_name", ""),
            mall_url=it.get("mall_url", ""),
            image_url=it.get("image_url", it.get("image", "")),
        )
        for it in outfit.get("items", [])
    ]

    scores_dict = outfit.get("scores")
    scores = None
    if scores_dict:
        scores = ScoresResponse(
            pcf=scores_dict.get("pcf", 0),
            of=scores_dict.get("of", 0),
            ch=scores_dict.get("ch", 0),
            pe=scores_dict.get("pe", 0),
            sf=scores_dict.get("sf", 0),
            total=scores_dict.get("total", 0),
        )

    return OutfitResponse(
        outfit_id=outfit.get("outfit_id", outfit.get("id", "")),
        items=items,
        scores=scores,
        reasons=outfit.get("reasons", []),
        tags=outfit.get("tags", []),
        is_complete_outfit=outfit.get("is_complete_outfit", False),
        total_price=outfit.get("total_price", 0),
    )
