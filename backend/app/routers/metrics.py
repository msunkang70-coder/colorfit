"""
Metrics API — POST /api/metrics
사용자 행동 측정 데이터 수집. MVP 검증 단계용.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api", tags=["metrics"])

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_LOG_PATH = _DATA_DIR / "metrics_log.jsonl"


class MetricsPayload(BaseModel):
    session_id: str = ""
    outfit_id: str = ""
    page_view_ts: str = ""
    decision_click_ts: str = ""
    ttd_ms: int = 0
    cta_clicked: bool = False
    trust_score: int = Field(0, ge=0, le=5)
    confidence: str = ""  # "yes" | "no" | "skip"
    tone_id: str = ""
    tpo: str = ""
    timestamp: str = ""


@router.post("/metrics")
async def post_metrics(payload: MetricsPayload) -> dict:
    """측정 데이터를 JSONL 파일에 append."""
    record = payload.model_dump()
    record["server_ts"] = datetime.utcnow().isoformat()

    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return {"status": "ok"}
