/**
 * Task 4.1v3 — selectDiverseTop3 + 축 기반 선발 단위 테스트.
 *
 * 시나리오 1~5 핵심 로직 + Edge Case 검증.
 */

import { describe, it, expect } from "vitest";
import {
  getTopAxis,
  calcSimilarity,
  getCatComboKey,
  selectDiverseTop3,
  AXIS_LABELS,
  type FeedOutfit,
} from "./feed-utils";

// ── 테스트 헬퍼 ──

function makeOutfit(overrides: Partial<FeedOutfit> & { outfit_id: string }): FeedOutfit {
  return {
    items: [
      { product_id: "p1", name: "니트", category: "knit", image_url: "", price: 30000, mall_url: "" },
      { product_id: "p2", name: "슬랙스", category: "slacks", image_url: "", price: 40000, mall_url: "" },
    ],
    scores: { pcf: 80, of: 70, ch: 60, pe: 50, sf: 75 },
    reasons: { core: "test core", evidence: "test evidence", risk_guard: "test guard" },
    tags: ["commute", "spring"],
    total_price: 70000,
    ...overrides,
  };
}

// ── getTopAxis ──

describe("getTopAxis", () => {
  it("scores가 null이면 pcf 반환", () => {
    expect(getTopAxis(null)).toBe("pcf");
  });

  it("pcf가 가장 높을 때 pcf 반환", () => {
    expect(getTopAxis({ pcf: 100, of: 50, ch: 50, pe: 50, sf: 50 })).toBe("pcf");
  });

  it("of가 가중 기여도 최고일 때 of 반환", () => {
    // of: 100*0.20=20, pcf: 50*0.25=12.5, sf: 50*0.25=12.5
    expect(getTopAxis({ pcf: 50, of: 100, ch: 50, pe: 50, sf: 50 })).toBe("of");
  });

  it("sf가 가중 기여도 최고일 때 sf 반환", () => {
    expect(getTopAxis({ pcf: 50, of: 50, ch: 50, pe: 50, sf: 100 })).toBe("sf");
  });

  it("ch만 높을 때 ch 반환", () => {
    // ch: 100*0.15=15, pcf: 30*0.25=7.5, of: 30*0.20=6, sf: 30*0.25=7.5
    expect(getTopAxis({ pcf: 30, of: 30, ch: 100, pe: 30, sf: 30 })).toBe("ch");
  });

  it("pe만 높을 때 pe 반환", () => {
    expect(getTopAxis({ pcf: 30, of: 30, ch: 30, pe: 100, sf: 30 })).toBe("pe");
  });

  it("optional 필드 누락 시 0으로 처리", () => {
    expect(getTopAxis({ pcf: 80, of: 70 })).toBe("pcf");
  });
});

// ── calcSimilarity ──

describe("calcSimilarity", () => {
  it("동일 TPO + 시즌 + 가격대 + 무드 → 최대 유사도 1.0", () => {
    const a = makeOutfit({ outfit_id: "a", tags: ["commute", "spring", "minimal"], total_price: 70000 });
    const b = makeOutfit({ outfit_id: "b", tags: ["commute", "spring", "minimal"], total_price: 70000 });
    expect(calcSimilarity(a, b)).toBe(1.0);
  });

  it("공통 태그 없으면 0", () => {
    const a = makeOutfit({ outfit_id: "a", tags: ["commute", "spring"], total_price: 70000 });
    const b = makeOutfit({ outfit_id: "b", tags: ["date", "autumn"], total_price: 200000 });
    expect(calcSimilarity(a, b)).toBe(0);
  });

  it("가격 ±30% 이내면 가격 유사도 포함", () => {
    const a = makeOutfit({ outfit_id: "a", tags: [], total_price: 100000 });
    const b = makeOutfit({ outfit_id: "b", tags: [], total_price: 120000 });
    expect(calcSimilarity(a, b)).toBeGreaterThan(0);
  });

  it("가격 ±30% 초과면 가격 유사도 제외", () => {
    const a = makeOutfit({ outfit_id: "a", tags: [], total_price: 100000 });
    const b = makeOutfit({ outfit_id: "b", tags: [], total_price: 200000 });
    expect(calcSimilarity(a, b)).toBe(0);
  });
});

// ── getCatComboKey ──

describe("getCatComboKey", () => {
  it("카테고리를 정렬 후 + 로 합침", () => {
    const outfit = makeOutfit({ outfit_id: "o1" });
    expect(getCatComboKey(outfit)).toBe("knit+slacks");
  });

  it("items 순서가 달라도 같은 키", () => {
    const o1 = makeOutfit({
      outfit_id: "o1",
      items: [
        { product_id: "p1", name: "A", category: "slacks", image_url: "", price: 0, mall_url: "" },
        { product_id: "p2", name: "B", category: "knit", image_url: "", price: 0, mall_url: "" },
      ],
    });
    expect(getCatComboKey(o1)).toBe("knit+slacks");
  });
});

// ── selectDiverseTop3 ──

describe("selectDiverseTop3", () => {
  // 시나리오 1: Decision Mode — Top1만 사용
  it("시나리오1: 코디 5개 입력 → Top1 rank=1, label='1위 추천'", () => {
    const outfits = [
      makeOutfit({ outfit_id: "o1", scores: { pcf: 95, of: 80, ch: 70, pe: 60, sf: 75 } }),
      makeOutfit({ outfit_id: "o2", scores: { pcf: 60, of: 90, ch: 70, pe: 60, sf: 70 }, items: [{ product_id: "p3", name: "셔츠", category: "shirt", image_url: "", price: 30000, mall_url: "" }] }),
      makeOutfit({ outfit_id: "o3", scores: { pcf: 70, of: 60, ch: 90, pe: 60, sf: 70 }, items: [{ product_id: "p4", name: "원피스", category: "dress", image_url: "", price: 50000, mall_url: "" }] }),
      makeOutfit({ outfit_id: "o4", scores: { pcf: 60, of: 60, ch: 60, pe: 95, sf: 60 }, items: [{ product_id: "p5", name: "자켓", category: "jacket", image_url: "", price: 20000, mall_url: "" }] }),
      makeOutfit({ outfit_id: "o5", scores: { pcf: 70, of: 60, ch: 60, pe: 60, sf: 90 }, items: [{ product_id: "p6", name: "코트", category: "coat", image_url: "", price: 80000, mall_url: "" }] }),
    ];
    const result = selectDiverseTop3(outfits);

    expect(result[0].outfit.outfit_id).toBe("o1");
    expect(result[0].rank).toBe(1);
    expect(result[0].label).toBe("1위 추천");
  });

  // 시나리오 2~3: Explore Mode — Top3 선발 다양성
  it("시나리오2-3: Top3 각각 서로 다른 outfit_id", () => {
    const outfits = [
      makeOutfit({ outfit_id: "o1", scores: { pcf: 95, of: 80, ch: 70, pe: 60, sf: 75 } }),
      makeOutfit({ outfit_id: "o2", scores: { pcf: 60, of: 95, ch: 70, pe: 60, sf: 70 }, items: [{ product_id: "p3", name: "셔츠", category: "shirt", image_url: "", price: 30000, mall_url: "" }] }),
      makeOutfit({ outfit_id: "o3", scores: { pcf: 70, of: 60, ch: 90, pe: 60, sf: 70 }, items: [{ product_id: "p4", name: "원피스", category: "dress", image_url: "", price: 50000, mall_url: "" }] }),
    ];
    const result = selectDiverseTop3(outfits);

    expect(result.length).toBe(3);
    const ids = result.map(r => r.outfit.outfit_id);
    expect(new Set(ids).size).toBe(3);
  });

  it("Top3의 rank가 1, 2, 3 순서", () => {
    const outfits = [
      makeOutfit({ outfit_id: "o1", scores: { pcf: 95, of: 60, ch: 60, pe: 60, sf: 60 } }),
      makeOutfit({ outfit_id: "o2", scores: { pcf: 60, of: 95, ch: 60, pe: 60, sf: 60 }, items: [{ product_id: "p3", name: "셔츠", category: "shirt", image_url: "", price: 30000, mall_url: "" }] }),
      makeOutfit({ outfit_id: "o3", scores: { pcf: 60, of: 60, ch: 60, pe: 60, sf: 95 }, items: [{ product_id: "p4", name: "코트", category: "coat", image_url: "", price: 80000, mall_url: "" }] }),
    ];
    const result = selectDiverseTop3(outfits);

    expect(result[0].rank).toBe(1);
    expect(result[1].rank).toBe(2);
    expect(result[2].rank).toBe(3);
  });

  it("Top2, Top3는 축 라벨이 AXIS_LABELS에서 매핑됨", () => {
    const outfits = [
      makeOutfit({ outfit_id: "o1", scores: { pcf: 95, of: 60, ch: 60, pe: 60, sf: 60 } }),
      makeOutfit({ outfit_id: "o2", scores: { pcf: 60, of: 95, ch: 60, pe: 60, sf: 60 }, items: [{ product_id: "p3", name: "셔츠", category: "shirt", image_url: "", price: 30000, mall_url: "" }] }),
      makeOutfit({ outfit_id: "o3", scores: { pcf: 60, of: 60, ch: 60, pe: 60, sf: 95 }, items: [{ product_id: "p4", name: "코트", category: "coat", image_url: "", price: 80000, mall_url: "" }] }),
    ];
    const result = selectDiverseTop3(outfits);

    const validLabels = [...Object.values(AXIS_LABELS), "1위 추천"];
    for (const r of result) {
      expect(validLabels).toContain(r.label);
    }
  });

  // 축 다양성 검증
  it("서로 다른 축의 코디가 있으면 Top3는 서로 다른 topAxis를 가짐", () => {
    const outfits = [
      makeOutfit({ outfit_id: "o1", scores: { pcf: 100, of: 30, ch: 30, pe: 30, sf: 30 } }),
      makeOutfit({ outfit_id: "o2", scores: { pcf: 30, of: 100, ch: 30, pe: 30, sf: 30 }, items: [{ product_id: "p3", name: "셔츠", category: "shirt", image_url: "", price: 30000, mall_url: "" }] }),
      makeOutfit({ outfit_id: "o3", scores: { pcf: 30, of: 30, ch: 30, pe: 30, sf: 100 }, items: [{ product_id: "p4", name: "코트", category: "coat", image_url: "", price: 80000, mall_url: "" }] }),
    ];
    const result = selectDiverseTop3(outfits);

    const axes = result.map(r => r.topAxis);
    expect(new Set(axes).size).toBe(3);
  });

  // 시나리오 5: TPO 변경 → 새 데이터로 재선발 (함수 자체는 stateless)
  it("시나리오5: 다른 입력 → 다른 Top1", () => {
    const commute = [makeOutfit({ outfit_id: "commute1", tags: ["commute"] })];
    const date = [makeOutfit({ outfit_id: "date1", tags: ["date"] })];

    const r1 = selectDiverseTop3(commute);
    const r2 = selectDiverseTop3(date);

    expect(r1[0].outfit.outfit_id).toBe("commute1");
    expect(r2[0].outfit.outfit_id).toBe("date1");
  });

  // Edge Case: 빈 배열
  it("빈 배열 → 빈 결과", () => {
    expect(selectDiverseTop3([])).toEqual([]);
  });

  // Edge Case: 코디 1개
  it("코디 1개 → Top1만 반환", () => {
    const result = selectDiverseTop3([makeOutfit({ outfit_id: "solo" })]);
    expect(result.length).toBe(1);
    expect(result[0].rank).toBe(1);
  });

  // Edge Case: 코디 2개
  it("코디 2개 → Top2까지만 반환", () => {
    const outfits = [
      makeOutfit({ outfit_id: "o1" }),
      makeOutfit({ outfit_id: "o2", items: [{ product_id: "p3", name: "셔츠", category: "shirt", image_url: "", price: 30000, mall_url: "" }] }),
    ];
    const result = selectDiverseTop3(outfits);
    expect(result.length).toBe(2);
    expect(result[0].rank).toBe(1);
    expect(result[1].rank).toBe(2);
  });

  // Edge Case: 모든 코디가 같은 축
  it("축 동일 시 fallback으로 순차 선택", () => {
    const outfits = [
      makeOutfit({ outfit_id: "o1", scores: { pcf: 95, of: 30, ch: 30, pe: 30, sf: 30 } }),
      makeOutfit({ outfit_id: "o2", scores: { pcf: 90, of: 30, ch: 30, pe: 30, sf: 30 }, items: [{ product_id: "p3", name: "셔츠", category: "shirt", image_url: "", price: 30000, mall_url: "" }] }),
      makeOutfit({ outfit_id: "o3", scores: { pcf: 85, of: 30, ch: 30, pe: 30, sf: 30 }, items: [{ product_id: "p4", name: "코트", category: "coat", image_url: "", price: 80000, mall_url: "" }] }),
    ];
    const result = selectDiverseTop3(outfits);

    expect(result.length).toBe(3);
    // fallback이어도 3개 모두 서로 다른 outfit
    const ids = result.map(r => r.outfit.outfit_id);
    expect(new Set(ids).size).toBe(3);
  });

  // Edge Case: scores가 null인 코디
  it("scores null → pcf로 fallback하여 정상 선발", () => {
    const outfits = [
      makeOutfit({ outfit_id: "o1", scores: null }),
      makeOutfit({ outfit_id: "o2", scores: { pcf: 60, of: 95, ch: 60, pe: 60, sf: 60 }, items: [{ product_id: "p3", name: "셔츠", category: "shirt", image_url: "", price: 30000, mall_url: "" }] }),
      makeOutfit({ outfit_id: "o3", scores: { pcf: 60, of: 60, ch: 60, pe: 60, sf: 95 }, items: [{ product_id: "p4", name: "코트", category: "coat", image_url: "", price: 80000, mall_url: "" }] }),
    ];
    const result = selectDiverseTop3(outfits);
    expect(result.length).toBe(3);
    expect(result[0].topAxis).toBe("pcf"); // null → fallback pcf
  });
});
