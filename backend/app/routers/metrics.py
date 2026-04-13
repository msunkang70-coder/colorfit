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


@router.get("/metrics/summary")
async def get_metrics_summary() -> dict:
    """수집된 측정 데이터 요약."""
    if not _LOG_PATH.exists():
        return {"total": 0, "records": []}

    records = []
    with open(_LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    # 요약 통계
    trust_scores = [r["trust_score"] for r in records if r.get("trust_score", 0) > 0]
    ttds = [r["ttd_ms"] for r in records if r.get("ttd_ms", 0) > 0]
    confidences = [r["confidence"] for r in records if r.get("confidence") and r["confidence"] != "skip"]

    return {
        "total": len(records),
        "trust_avg": round(sum(trust_scores) / len(trust_scores), 1) if trust_scores else 0,
        "ttd_median_ms": sorted(ttds)[len(ttds) // 2] if ttds else 0,
        "confidence_yes_rate": round(sum(1 for c in confidences if c == "yes") / len(confidences) * 100, 1) if confidences else 0,
        "records": records,
    }
