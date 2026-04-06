"""Task 4.1v3 — 통합 테스트: Feed API + Reason Generator."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


# ──────────────────────────────────────────────
# Feed API 통합 테스트
# ──────────────────────────────────────────────

class TestFeedAPIPageSize:
    """Feed API page_size 파라미터 응답 검증."""

    BASE_PARAMS = {
        "tone_id": "spring_warm_light",
        "tpo": "commute",
        "gender": "female",
        "budget_min": 0,
        "budget_max": 500000,
    }

    def test_page_size_3(self):
        """page_size=3 → 최대 3개 코디 반환."""
        resp = client.get("/api/feed", params={**self.BASE_PARAMS, "page_size": 3})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["outfits"]) <= 3

    def test_page_size_5(self):
        """page_size=5 → 최대 5개 코디 반환."""
        resp = client.get("/api/feed", params={**self.BASE_PARAMS, "page_size": 5})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["outfits"]) <= 5

    def test_page_size_1(self):
        """page_size=1 → Decision Mode 전용, 1개만."""
        resp = client.get("/api/feed", params={**self.BASE_PARAMS, "page_size": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["outfits"]) <= 1

    def test_default_page_size(self):
        """page_size 미지정 → 기본값 동작."""
        resp = client.get("/api/feed", params=self.BASE_PARAMS)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["outfits"]) >= 1


class TestFeedAPIResponse:
    """Feed API 응답 구조 검증."""

    BASE_PARAMS = {
        "tone_id": "spring_warm_light",
        "tpo": "commute",
        "gender": "female",
        "page_size": 5,
    }

    def test_outfit_has_scores(self):
        """각 코디에 5축 scores가 포함되어야 한다."""
        resp = client.get("/api/feed", params=self.BASE_PARAMS)
        data = resp.json()
        if data["outfits"]:
            outfit = data["outfits"][0]
            scores = outfit.get("scores") or {}
            for axis in ["pcf", "of", "ch", "pe", "sf"]:
                assert axis in scores, f"Missing score axis: {axis}"

    def test_outfit_has_reasons(self):
        """각 코디에 reasons(core/evidence/risk_guard)가 포함되어야 한다."""
        resp = client.get("/api/feed", params=self.BASE_PARAMS)
        data = resp.json()
        if data["outfits"]:
            outfit = data["outfits"][0]
            reasons = outfit.get("reasons")
            assert reasons is not None, "Missing reasons"
            assert "core" in reasons, "Missing core"
            assert "evidence" in reasons, "Missing evidence"
            assert "risk_guard" in reasons, "Missing risk_guard"

    def test_outfit_has_items(self):
        """각 코디에 items 배열이 있어야 한다."""
        resp = client.get("/api/feed", params=self.BASE_PARAMS)
        data = resp.json()
        if data["outfits"]:
            outfit = data["outfits"][0]
            assert "items" in outfit
            assert len(outfit["items"]) >= 1

    def test_outfits_sorted_by_total(self):
        """코디는 total score 내림차순이어야 한다."""
        resp = client.get("/api/feed", params=self.BASE_PARAMS)
        data = resp.json()
        outfits = data["outfits"]
        if len(outfits) >= 2:
            totals = []
            for o in outfits:
                scores = o.get("scores") or {}
                totals.append(scores.get("total", 0))
            for i in range(len(totals) - 1):
                assert totals[i] >= totals[i + 1], \
                    f"Not sorted: {totals[i]} < {totals[i+1]}"


class TestFeedAPITPO:
    """TPO별 Feed API 동작 검증."""

    TPOS = ["commute", "date", "interview", "weekend", "workout",
            "travel", "event", "campus"]

    @pytest.mark.parametrize("tpo", TPOS)
    def test_tpo_returns_outfits(self, tpo):
        """각 TPO에서 최소 1개 코디 반환."""
        resp = client.get("/api/feed", params={
            "tone_id": "spring_warm_light",
            "tpo": tpo,
            "gender": "female",
            "page_size": 5,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["outfits"]) >= 1, f"No outfits for tpo={tpo}"


class TestFeedAPIEdgeCases:
    """Feed API 엣지 케이스 검증."""

    def test_extreme_budget_returns_some(self):
        """극단적 예산에서도 에러 없이 응답."""
        resp = client.get("/api/feed", params={
            "tone_id": "spring_warm_light",
            "tpo": "commute",
            "gender": "female",
            "budget_min": 0,
            "budget_max": 10000,
            "page_size": 5,
        })
        assert resp.status_code == 200

    def test_male_gender(self):
        """남성 필터도 정상 동작."""
        resp = client.get("/api/feed", params={
            "tone_id": "autumn_warm_deep",
            "tpo": "commute",
            "gender": "male",
            "page_size": 5,
        })
        assert resp.status_code == 200


# ──────────────────────────────────────────────
# Reason Generator 다양성 테스트
# ──────────────────────────────────────────────

class TestReasonDiversity:
    """서로 다른 outfit → 서로 다른 evidence 확인."""

    def test_different_outfits_different_evidence(self):
        """Top5 코디의 evidence가 모두 동일하지 않아야 한다."""
        resp = client.get("/api/feed", params={
            "tone_id": "spring_warm_light",
            "tpo": "commute",
            "gender": "female",
            "page_size": 5,
        })
        data = resp.json()
        outfits = data["outfits"]
        if len(outfits) >= 2:
            evidences = []
            for o in outfits:
                reasons = o.get("reasons")
                if reasons and reasons.get("evidence"):
                    ev = reasons["evidence"]
                    evidences.append(ev[0] if isinstance(ev, list) else ev)
            # 최소 2개 이상의 서로 다른 evidence가 있어야
            unique = set(evidences)
            assert len(unique) >= min(2, len(evidences)), \
                f"All evidence identical: {evidences[:3]}"

    def test_reasons_have_content(self):
        """reason의 각 파트가 빈 문자열이 아니어야 한다."""
        resp = client.get("/api/feed", params={
            "tone_id": "summer_cool_soft",
            "tpo": "date",
            "gender": "female",
            "page_size": 3,
        })
        data = resp.json()
        for o in data["outfits"]:
            reasons = o.get("reasons")
            if reasons:
                assert reasons.get("core"), "Empty core"
                assert reasons.get("evidence"), "Empty evidence"
                assert reasons.get("risk_guard"), "Empty risk_guard"


# ──────────────────────────────────────────────
# Metrics API 테스트
# ──────────────────────────────────────────────

class TestMetricsAPI:
    """측정 데이터 전송 검증."""

    def test_post_metrics(self):
        """MetricsPayload 전송 → 200 OK."""
        payload = {
            "session_id": "test_session_001",
            "outfit_id": "outfit_sw_001",
            "page_view_ts": "2026-04-06T10:00:00.000Z",
            "decision_click_ts": "2026-04-06T10:00:12.000Z",
            "ttd_ms": 12000,
            "cta_clicked": True,
            "trust_score": 4,
            "confidence": "yes",
            "expanded": True,
            "expand_level": 1,
            "selected_rank": 2,
            "tone_id": "spring_warm_light",
            "tpo": "commute",
        }
        resp = client.post("/api/metrics", json=payload)
        assert resp.status_code == 200

    def test_post_metrics_decision_mode(self):
        """Decision Mode 측정: expanded=false, rank=1."""
        payload = {
            "session_id": "test_session_002",
            "outfit_id": "outfit_sw_002",
            "ttd_ms": 8000,
            "cta_clicked": True,
            "trust_score": 5,
            "confidence": "yes",
            "expanded": False,
            "expand_level": 0,
            "selected_rank": 1,
        }
        resp = client.post("/api/metrics", json=payload)
        assert resp.status_code == 200

    def test_post_metrics_skip_survey(self):
        """설문 스킵: trust_score 미포함, confidence=skip."""
        payload = {
            "session_id": "test_session_003",
            "outfit_id": "outfit_sw_003",
            "ttd_ms": 5000,
            "cta_clicked": True,
            "confidence": "skip",
            "expanded": False,
            "expand_level": 0,
            "selected_rank": 1,
        }
        resp = client.post("/api/metrics", json=payload)
        assert resp.status_code == 200
