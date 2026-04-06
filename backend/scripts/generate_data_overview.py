"""데이터 센스체크용 통합 개요 파일 생성.

TPO별 Top5 코디를 이미지 링크 포함하여 Markdown으로 출력.
사용법:
  cd backend
  .venv/Scripts/python scripts/generate_data_overview.py
  → docs/DATA_OVERVIEW.md 생성
"""

import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "backend" / "data"
OUT_PATH = ROOT / "docs" / "DATA_OVERVIEW.md"

TPOS = ["commute", "interview", "date", "campus", "weekend", "travel", "event", "workout"]
TPO_KR = {
    "commute": "출근", "interview": "면접", "date": "데이트",
    "campus": "캠퍼스", "weekend": "주말", "travel": "여행",
    "event": "행사", "workout": "운동",
}
AXIS_KR = {"pcf": "컬러매칭", "of": "상황적합", "ch": "색조화", "pe": "가성비", "sf": "실루엣"}


def load_outfits():
    return json.loads((DATA_DIR / "outfits_scored.json").read_text(encoding="utf-8"))


def get_top_axis(scores: dict) -> str:
    axes = ["pcf", "of", "ch", "pe", "sf"]
    return max(axes, key=lambda a: scores.get(a, 0))


def format_price(p: int) -> str:
    if p >= 10000:
        return f"{p // 10000}만{(p % 10000) // 1000}천" if p % 10000 else f"{p // 10000}만"
    return f"{p:,}원"


def generate():
    outfits = load_outfits()
    lines = []
    w = lines.append

    w("# ColorFit 데이터 개요 (센스체크용)")
    w("")
    w(f"> 자동 생성일: 2026-04-06")
    w(f"> 총 코디: {len(outfits)}개")
    w(f"> 스코어 완료: {sum(1 for o in outfits if o.get('scores') and o['scores'].get('total'))}개")
    w("")

    # ── 전체 요약 ──
    w("## 전체 요약")
    w("")
    w("| TPO | 한글 | 여성 | 남성 | 합계 | 대표 스타일 | formality 범위 | 평균 가격 |")
    w("|-----|------|------|------|------|-----------|---------------|----------|")

    for tpo in TPOS:
        f_list = [o for o in outfits if o.get("designed_tpo") and tpo in [t.lower() for t in o["designed_tpo"]]
                  and o.get("gender") == "female" and o.get("scores") and o["scores"].get("total")]
        m_list = [o for o in outfits if o.get("designed_tpo") and tpo in [t.lower() for t in o["designed_tpo"]]
                  and o.get("gender") == "male" and o.get("scores") and o["scores"].get("total")]
        total = f_list + m_list

        styles = Counter(o.get("style_tag", "") for o in total).most_common(3)
        style_str = ", ".join(f"{s}({c})" for s, c in styles)

        formals = [o.get("formality_avg", 0) for o in total if o.get("formality_avg")]
        f_range = f"{min(formals):.1f}~{max(formals):.1f}" if formals else "-"

        prices = [o.get("price_total") or o.get("total_price") or 0 for o in total]
        prices = [p for p in prices if p > 0]
        avg_price = f"{sum(prices) // len(prices) // 1000}K" if prices else "-"

        w(f"| {tpo} | {TPO_KR[tpo]} | {len(f_list)} | {len(m_list)} | {len(total)} | {style_str} | {f_range} | {avg_price} |")

    w("")

    # ── TPO별 상세 ──
    for tpo in TPOS:
        w(f"---")
        w(f"")
        w(f"## {TPO_KR[tpo]} ({tpo})")
        w("")

        for gender, gender_kr in [("female", "여성"), ("male", "남성")]:
            filtered = [o for o in outfits
                        if o.get("designed_tpo") and tpo in [t.lower() for t in o["designed_tpo"]]
                        and o.get("gender") == gender
                        and o.get("scores") and o["scores"].get("total")]
            filtered.sort(key=lambda x: x["scores"]["total"], reverse=True)

            if not filtered:
                continue

            top5 = filtered[:5]
            w(f"### {gender_kr} Top5 ({len(filtered)}개 중)")
            w("")

            for rank, o in enumerate(top5, 1):
                s = o["scores"]
                cats = [it.get("category", "?") for it in o.get("items", [])]
                style = o.get("style_tag", "")
                tone = o.get("tone_id", "")
                price = o.get("price_total") or o.get("total_price") or 0
                top_axis = get_top_axis(s)
                formality = o.get("formality_avg", 0)

                # 이미지 URL 수집
                images = []
                for it in o.get("items", []):
                    img = it.get("image_url", "")
                    if img:
                        images.append(img)

                w(f"**{rank}위** | 총점 {s['total']:.1f} | {AXIS_KR[top_axis]}형 | {style}")
                w(f"")
                w(f"| 항목 | 값 |")
                w(f"|------|-----|")
                w(f"| ID | `{o.get('outfit_id', '')[:50]}` |")
                w(f"| 아이템 | {' + '.join(cats)} |")
                w(f"| 톤 | {tone} |")
                w(f"| 가격 | {price:,}원 |")
                w(f"| formality | {formality:.1f} |")
                w(f"| 스코어 | PCF={s['pcf']:.0f} OF={s['of']:.0f} CH={s['ch']:.0f} PE={s['pe']:.0f} SF={s['sf']:.0f} |")
                w(f"| 스타일 태그 | {', '.join(o.get('tags', []))} |")

                if images:
                    w(f"| 이미지 | ", )
                    for idx, img in enumerate(images[:4]):
                        lines[-1] += f"[아이템{idx+1}]({img}) "
                    lines[-1] += "|"
                else:
                    w(f"| 이미지 | (없음) |")

                w("")

            # 카테고리 분포
            all_cats = []
            for o in filtered:
                for it in o.get("items", []):
                    all_cats.append(it.get("category", "?"))
            cat_dist = Counter(all_cats).most_common(8)
            w(f"**카테고리 분포:** {', '.join(f'{c}({n})' for c, n in cat_dist)}")
            w("")

            # 스타일 분포
            style_dist = Counter(o.get("style_tag", "") for o in filtered).most_common(5)
            w(f"**스타일 분포:** {', '.join(f'{s}({n})' for s, n in style_dist)}")
            w("")

    # ── 스코어 분포 전체 ──
    w("---")
    w("")
    w("## 스코어 분포 (전체)")
    w("")
    scored = [o for o in outfits if o.get("scores") and o["scores"].get("total")]
    for axis in ["pcf", "of", "ch", "pe", "sf", "total"]:
        vals = [o["scores"][axis] for o in scored if axis in o["scores"]]
        if vals:
            vals.sort()
            unique = len(set(round(v, 1) for v in vals))
            w(f"- **{axis}**: min={min(vals):.1f}, median={vals[len(vals)//2]:.1f}, max={max(vals):.1f}, unique={unique}")
    w("")

    # 저장
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated: {OUT_PATH} ({len(lines)} lines)")


if __name__ == "__main__":
    generate()
