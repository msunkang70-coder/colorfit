/**
 * Feed 페이지 순수 함수 — selectDiverseTop3 등 축 기반 Top3 선발 로직.
 */

const AXIS_LABELS: Record<string, string> = {
  pcf: "컬러 매칭형",
  of: "상황 최적형",
  ch: "색감 조화형",
  pe: "가성비형",
  sf: "실루엣형",
};

const AXIS_WEIGHTS: Record<string, number> = {
  pcf: 0.25, of: 0.20, ch: 0.15, pe: 0.15, sf: 0.25,
};

export interface FeedScores {
  pcf: number;
  of: number;
  ch?: number;
  pe?: number;
  sf?: number;
}

export interface FeedOutfit {
  outfit_id: string;
  items: {
    product_id: string;
    name: string;
    category: string;
    image_url: string;
    price: number;
    mall_url: string;
  }[];
  scores: FeedScores | null;
  reasons: { core: string; evidence: string; risk_guard: string } | null;
  tags: string[];
  total_price: number;
}

export interface RankedOutfit {
  outfit: FeedOutfit;
  topAxis: string;
  label: string;
  rank: number;
}

const TPO_SET = new Set(["commute", "interview", "date", "weekend", "campus", "travel", "event", "workout"]);
const SEASON_SET = new Set(["spring", "summer", "autumn", "winter"]);

export function getTopAxis(scores: FeedScores | null): string {
  if (!scores) return "pcf";
  let best = "pcf";
  let bestContrib = -1;
  for (const axis of ["pcf", "of", "ch", "pe", "sf"] as const) {
    const raw = scores[axis] ?? 0;
    const w = AXIS_WEIGHTS[axis] ?? 0;
    const contrib = raw * w;
    if (contrib > bestContrib) {
      best = axis;
      bestContrib = contrib;
    }
  }
  return best;
}

export function calcSimilarity(anchor: FeedOutfit, candidate: FeedOutfit): number {
  let score = 0;
  const anchorTags = anchor.tags ?? [];
  const candTags = candidate.tags ?? [];

  const aTpo = anchorTags.filter(t => TPO_SET.has(t));
  const cTpo = candTags.filter(t => TPO_SET.has(t));
  if (aTpo.some(t => cTpo.includes(t))) score += 1.5;

  const aSeason = anchorTags.filter(t => SEASON_SET.has(t));
  const cSeason = candTags.filter(t => SEASON_SET.has(t));
  if (aSeason.some(t => cSeason.includes(t))) score += 1.0;

  if (anchor.total_price > 0 && candidate.total_price > 0) {
    const ratio = candidate.total_price / anchor.total_price;
    if (ratio >= 0.7 && ratio <= 1.3) score += 0.5;
  }

  const aMood = anchorTags.filter(t => !TPO_SET.has(t) && !SEASON_SET.has(t));
  const cMood = candTags.filter(t => !TPO_SET.has(t) && !SEASON_SET.has(t));
  if (aMood.some(t => cMood.includes(t))) score += 1.0;

  return score / 4;
}

export function getCatComboKey(outfit: FeedOutfit): string {
  return outfit.items.map(it => it.category || "").sort().join("+");
}

export function selectDiverseTop3(outfits: FeedOutfit[]): RankedOutfit[] {
  if (outfits.length === 0) return [];

  const top1 = outfits[0];
  const top1Axis = getTopAxis(top1.scores);
  const top1Combo = getCatComboKey(top1);
  const result: RankedOutfit[] = [
    { outfit: top1, topAxis: top1Axis, label: "1위 추천", rank: 1 },
  ];

  if (outfits.length === 1) return result;

  const candidates = outfits.slice(1).map(o => ({
    outfit: o,
    axis: getTopAxis(o.scores),
    similarity: calcSimilarity(top1, o),
    combo: getCatComboKey(o),
  }));

  const similar = candidates.filter(c => c.similarity >= 0.5);
  const pool = similar.length >= 2 ? similar : candidates;

  const usedAxes = new Set([top1Axis]);
  const usedIds = new Set([top1.outfit_id]);
  const usedCombos = new Set([top1Combo]);

  const diffComboAxis = pool.find(c => !usedCombos.has(c.combo) && !usedAxes.has(c.axis) && !usedIds.has(c.outfit.outfit_id));
  const diffCombo = pool.find(c => !usedCombos.has(c.combo) && !usedIds.has(c.outfit.outfit_id));
  const pick2 = diffComboAxis ?? diffCombo ?? pool.find(c => !usedIds.has(c.outfit.outfit_id));

  if (pick2) {
    result.push({ outfit: pick2.outfit, topAxis: pick2.axis, label: AXIS_LABELS[pick2.axis] ?? pick2.axis, rank: 2 });
    usedAxes.add(pick2.axis);
    usedIds.add(pick2.outfit.outfit_id);
    usedCombos.add(pick2.combo);
  }

  const remaining = pool.filter(c => !usedIds.has(c.outfit.outfit_id));
  const pick3combo = remaining.find(c => !usedCombos.has(c.combo) && !usedAxes.has(c.axis));
  const pick3any = remaining.find(c => !usedCombos.has(c.combo));
  const pick3 = pick3combo ?? pick3any ?? remaining[0];

  if (pick3) {
    result.push({ outfit: pick3.outfit, topAxis: pick3.axis, label: AXIS_LABELS[pick3.axis] ?? pick3.axis, rank: 3 });
  }

  return result;
}

export { AXIS_LABELS, AXIS_WEIGHTS };
