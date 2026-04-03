"""
Feed API — GET /api/feed
전체 파이프라인: Profile Load → Hard Filter → StyleFilter → Score → Rerank → Reason
기획서 섹션 6.1 참조.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Query

from app.schemas.outfit import FeedResponse, OutfitResponse, ScoresResponse, ItemResponse, ReasonResponse
from app.services.feed_builder import (
    apply_hard_filters, score_and_rerank,
    stage1_hard_filter, stage2_eligibility, stage3_soft_score, stage4_expert_rerank,
)
from app.services.reason_generator import generate_reasons
from app.services.stylist_rules import apply_stylist_rules
from app.services.quality_filters import apply_quality_filters
from app.services.qa_gate import qa_check

router = APIRouter(prefix="/api", tags=["feed"])

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"

_outfits_cache: list[dict] | None = None


def _load_outfits_from_json() -> list[dict]:
    """코디 데이터를 로드한다 (MVP용). scored > evaluated > raw 순. 캐싱 적용."""
    global _outfits_cache
    if _outfits_cache is not None:
        return copy.deepcopy(_outfits_cache)

    for name in ("outfits_scored.json", "outfits_evaluated.json", "outfits.json"):
        path = _DATA_DIR / name
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                _outfits_cache = json.load(f)
            return copy.deepcopy(_outfits_cache)
    return []


def _outfit_to_response(outfit: dict) -> OutfitResponse:
    """내부 코디 딕셔너리를 응답 DTO로 변환."""
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
            total=scores_dict.get("reranked_total", scores_dict.get("total", 0)),
        )

    # reasons: ReasonResult dict → ReasonResponse
    raw_reasons = outfit.get("reasons")
    reason_resp = None
    if isinstance(raw_reasons, dict):
        reason_resp = ReasonResponse(
            core=raw_reasons.get("core", ""),
            evidence=raw_reasons.get("evidence", ""),
            risk_guard=raw_reasons.get("risk_guard", ""),
        )

    return OutfitResponse(
        outfit_id=outfit.get("outfit_id", outfit.get("id", "")),
        items=items,
        scores=scores,
        reasons=reason_resp,
        tags=outfit.get("tags", []),
        is_complete_outfit=outfit.get("is_complete_outfit", False),
        total_price=outfit.get("total_price", 0),
    )


@router.get("/feed", response_model=FeedResponse)
async def get_feed(
    tone_id: str = Query("", description="사용자 퍼스널컬러 톤 ID"),
    tpo: str = Query("", description="TPO 쉼표 구분 (office,casual)"),
    gender: str = Query("", description="성별 (female/male)"),
    budget_min: float = Query(0, ge=0),
    budget_max: float = Query(300000, ge=0),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
) -> FeedResponse:
    """코디 피드 — 전체 추천 파이프라인 실행."""
    tpo_list = [t.strip() for t in tpo.split(",") if t.strip()] if tpo else []

    # 1. 코디 로드 (MVP: JSON 파일, 캐싱)
    all_outfits = _load_outfits_from_json()

    # Stage 1: Hard Filter (성별, 예산, 계절)
    hard_filtered = stage1_hard_filter(all_outfits, user_gender=gender, budget_max=budget_max)

    # Stage 2: Eligibility (TPO, 브랜드, 톤, 스타일) + 최소 보장
    eligible = stage2_eligibility(hard_filtered, user_tone_id=tone_id, user_tpo_list=tpo_list)

    # Quality Filters: 비의류/브랜드등급/연령키워드
    quality_filtered = apply_quality_filters(eligible, tpo_list)

    # Stylist Rules: TPO별 금기/포멀도 적용
    styled = apply_stylist_rules(quality_filtered, tpo_list)

    # Stage 3: Soft Score (5축 가중합 + 정렬)
    scored = stage3_soft_score(
        styled, user_tone_id=tone_id, user_tpo_list=tpo_list,
        budget_min=budget_min, budget_max=budget_max,
    )

    # Stage 4: Expert Rerank (다양성, 중복 제거)
    ranked = stage4_expert_rerank(scored, user_tpo_list=tpo_list)

    # QA Gate: 성별/시즌/포멀도 최종 검증
    qa_passed = qa_check(ranked, user_gender=gender, user_tpo_list=tpo_list)

    # 7. Reason Gen (페이지 단위)
    total_count = len(qa_passed)
    start = (page - 1) * page_size
    end = start + page_size
    page_outfits = qa_passed[start:end]

    for outfit in page_outfits:
        scores = outfit.get("scores", {})
        outfit_items = outfit.get("items", [])
        reasons = generate_reasons(
            scores,
            items=outfit_items,
            user_tone_id=tone_id,
            user_tpo_list=tpo_list,
        )
        outfit["reasons"] = reasons

    # 응답 변환
    response_outfits = [_outfit_to_response(o) for o in page_outfits]

    return FeedResponse(
        outfits=response_outfits,
        total_count=total_count,
        page=page,
        page_size=page_size,
        has_next=end < total_count,
    )
