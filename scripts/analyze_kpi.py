"""KPI 분석 스크립트 — CSV 기반 측정 데이터 분석.

사용법:
  python scripts/analyze_kpi.py [metrics.jsonl 경로]
  기본: backend/data/metrics.jsonl
"""

import json
import sys
from pathlib import Path
from collections import Counter


def load_metrics(path: str) -> list[dict]:
    records = []
    p = Path(path)
    if not p.exists():
        print(f"파일 없음: {path}")
        return records
    for line in p.read_text(encoding="utf-8").strip().split("\n"):
        if line.strip():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def analyze(records: list[dict]) -> None:
    if not records:
        print("측정 데이터 없음. 사용자 테스트 후 다시 실행하세요.")
        return

    total = len(records)
    print(f"=== ColorFit KPI 분석 ===")
    print(f"총 세션: {total}")
    print()

    # 1. TTD 분석
    decision_ttds = [r["ttd_ms"] for r in records if r.get("ttd_ms") and not r.get("expanded")]
    explore_ttds = [r["ttd_ms"] for r in records if r.get("ttd_ms") and r.get("expanded")]

    if decision_ttds:
        decision_ttds.sort()
        med = decision_ttds[len(decision_ttds) // 2]
        print(f"[TTD - Decision Mode]")
        print(f"  중앙값: {med / 1000:.1f}초 (목표 < 15초) {'PASS' if med < 15000 else 'FAIL'}")
        print(f"  평균: {sum(decision_ttds) / len(decision_ttds) / 1000:.1f}초")
        print(f"  샘플: {len(decision_ttds)}건")
        print()

    if explore_ttds:
        explore_ttds.sort()
        med = explore_ttds[len(explore_ttds) // 2]
        print(f"[TTD - Explore Mode]")
        print(f"  중앙값: {med / 1000:.1f}초 (목표 < 30초) {'PASS' if med < 30000 else 'FAIL'}")
        print(f"  평균: {sum(explore_ttds) / len(explore_ttds) / 1000:.1f}초")
        print(f"  샘플: {len(explore_ttds)}건")
        print()

    # 2. CTR
    cta_clicked = sum(1 for r in records if r.get("cta_clicked"))
    ctr = cta_clicked / total * 100
    print(f"[CTR]")
    print(f"  {ctr:.1f}% (목표 > 30%) {'PASS' if ctr > 30 else 'FAIL'}")
    print()

    # 3. 신뢰도
    trust_scores = [r["trust_score"] for r in records if r.get("trust_score")]
    if trust_scores:
        avg_trust = sum(trust_scores) / len(trust_scores)
        print(f"[신뢰도]")
        print(f"  평균: {avg_trust:.2f} (목표 >= 4.0) {'PASS' if avg_trust >= 4.0 else 'FAIL'}")
        print(f"  분포: {Counter(trust_scores)}")
        print()

    # 4. 실행 확신
    conf = [r["confidence"] for r in records if r.get("confidence")]
    if conf:
        yes_count = sum(1 for c in conf if c == "yes")
        yes_pct = yes_count / len(conf) * 100
        print(f"[실행 확신]")
        print(f"  Yes: {yes_pct:.1f}% (목표 >= 70%) {'PASS' if yes_pct >= 70 else 'FAIL'}")
        print(f"  분포: {Counter(conf)}")
        print()

    # 5. Explore 진입율
    expanded_count = sum(1 for r in records if r.get("expanded"))
    expanded_pct = expanded_count / total * 100
    print(f"[Explore 진입율]")
    print(f"  {expanded_pct:.1f}% (측정)")
    print()

    # 6. selected_rank 분포
    ranks = [r["selected_rank"] for r in records if r.get("selected_rank")]
    if ranks:
        rank1_pct = sum(1 for r in ranks if r == 1) / len(ranks) * 100
        print(f"[Top1 선택율]")
        print(f"  {rank1_pct:.1f}% (목표 >= 60%) {'PASS' if rank1_pct >= 60 else 'FAIL'}")
        print(f"  분포: {Counter(ranks)}")
        print()

    # 7. 가설별 판정
    print(f"=== 가설 검증 요약 ===")
    if decision_ttds:
        med = decision_ttds[len(decision_ttds) // 2]
        print(f"  H1 (TTD < 15초): {'PASS' if med < 15000 else 'FAIL'} ({med/1000:.1f}초)")
    if trust_scores:
        avg = sum(trust_scores) / len(trust_scores)
        print(f"  H2 (신뢰도 >= 4.0): {'PASS' if avg >= 4.0 else 'FAIL'} ({avg:.2f})")
    if trust_scores and explore_ttds:
        dec_trust = [r["trust_score"] for r in records if r.get("trust_score") and not r.get("expanded")]
        exp_trust = [r["trust_score"] for r in records if r.get("trust_score") and r.get("expanded")]
        if dec_trust and exp_trust:
            d_avg = sum(dec_trust) / len(dec_trust)
            e_avg = sum(exp_trust) / len(exp_trust)
            print(f"  H3 (Explore trust > Decision): {'PASS' if e_avg >= d_avg else 'FAIL'} (D={d_avg:.2f}, E={e_avg:.2f})")
    if ranks:
        r1 = sum(1 for r in ranks if r == 1) / len(ranks) * 100
        print(f"  H4 (Top1 >= 60%): {'PASS' if r1 >= 60 else 'FAIL'} ({r1:.1f}%)")
    if conf:
        yes_pct = sum(1 for c in conf if c == "yes") / len(conf) * 100
        print(f"  H5 (확신 Yes >= 70%): {'PASS' if yes_pct >= 70 else 'FAIL'} ({yes_pct:.1f}%)")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "backend/data/metrics.jsonl"
    records = load_metrics(path)
    analyze(records)
