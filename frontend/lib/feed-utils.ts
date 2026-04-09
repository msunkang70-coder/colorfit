/**
 * Feed 페이지 순수 함수 — selectDiverseTop3 등 축 기반 Top3 선발 로직.
 */

const AXIS_LABELS: Record<string, string> = {
  tpo: "TPO 최적형",
  fit: "핏 추천형",
  color: "컬러 매칭형",
  style: "스타일 통일형",
  // 기존 호환
  pcf: "컬러 매칭형",
  of: "상황 최적형",
  ch: "색감 조화형",
  pe: "가성비형",
  sf: "실루엣형",
};

const AXIS_DESC: Record<string, string> = {
  tpo: "TPO 적합도가 더 높은 대안",
  fit: "핏 밸런스가 더 좋은 대안",
  color: "컬러 조합이 더 좋은 대안",
  style: "스타일 일관성이 더 높은 대안",
  pcf: "퍼스널컬러 적합도가 더 높은 대안",
  of: "TPO 적합도가 더 높은 대안",
  ch: "아이템 간 컬러 조화가 더 좋은 대안",
  pe: "가격 대비 만족도가 더 높은 대안",
  sf: "핏 밸런스가 더 좋은 대안",
};

const AXIS_WEIGHTS: Record<string, number> = {
  tpo: 0.30, fit: 0.15, color: 0.20, style: 0.20,
  // 기존 호환 (selectDiverseTop3에서 사용)
  pcf: 0.20, of: 0.30, ch: 0.15, pe: 0.10, sf: 0.25,
};

export interface FeedScores {
  // v2
  tpo?: number;
  fit?: number;
  color?: number;
  style?: number;
  risk?: number;
  final?: number;
  // v1 호환
  pcf: number;
  of: number;
  ch?: number;
  pe?: number;
  sf?: number;
  total?: number;
}

export interface FeedOutfit {
  outfit_id: string;
  items: {
    product_id: string;
    name: string;
    category: string;
    image_url: string;
    price: number;
    brand?: string;
    mall_url?: string;
    style_tag?: string;
    formality?: number;
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
  diffDesc?: string;
  rank: number;
}

const TPO_SET = new Set(["commute", "interview", "date", "weekend", "campus", "travel", "event", "workout"]);

// ── 스타일 일관성 후처리 필터 ──

const FORMAL_CATS = new Set(["셔츠", "블라우스", "슬랙스", "자켓", "코트", "로퍼", "힐", "넥타이", "정장바지"]);
const CASUAL_CATS = new Set(["후드", "맨투맨", "청바지", "반바지", "조거팬츠", "스니커즈", "크롭탑"]);
const SPORT_CATS = new Set(["레깅스", "트레이닝팬츠", "스포츠브라", "반팔티", "바람막이"]);

const FORMAL_TPOS = new Set(["interview", "event", "commute"]);

type StyleGroup = "formal" | "casual" | "sport" | "neutral";

function classifyItemStyle(category: string, styleTag?: string): StyleGroup {
  // style_tag가 있으면 우선 사용
  if (styleTag) {
    const t = styleTag.toLowerCase();
    if (["formal", "classic", "minimal"].includes(t)) return "formal";
    if (["sporty", "athletic"].includes(t)) return "sport";
    if (["casual", "street"].includes(t)) return "casual";
  }
  // fallback: 카테고리 기반
  if (FORMAL_CATS.has(category)) return "formal";
  if (CASUAL_CATS.has(category)) return "casual";
  if (SPORT_CATS.has(category)) return "sport";
  return "neutral";
}

export interface StyleCheck {
  pass: boolean;
  dominant: StyleGroup;
  ratio: number;
  conflict: string;
  formalityStd: number;  // 포멀도 표준편차
}

export function checkStyleConsistency(outfit: FeedOutfit, tpo: string): StyleCheck {
  const items = outfit.items ?? [];
  if (items.length === 0) return { pass: true, dominant: "neutral", ratio: 1, conflict: "", formalityStd: 0 };

  // 1) 스타일 그룹 분류 (style_tag 우선)
  const counts: Record<StyleGroup, number> = { formal: 0, casual: 0, sport: 0, neutral: 0 };
  for (const it of items) {
    counts[classifyItemStyle(it.category ?? "", it.style_tag)] += 1;
  }

  const total = items.length;
  const entries = Object.entries(counts) as [StyleGroup, number][];
  entries.sort((a, b) => b[1] - a[1]);
  const [dominant, dominantCount] = entries[0];
  const ratio = dominantCount / total;

  // 2) 포멀도 일관성 (formality 필드 활용)
  const formalities = items.map(it => it.formality ?? 0).filter(f => f > 0);
  let formalityStd = 0;
  if (formalities.length >= 2) {
    const avg = formalities.reduce((a, b) => a + b, 0) / formalities.length;
    formalityStd = Math.sqrt(formalities.reduce((s, f) => s + (f - avg) ** 2, 0) / formalities.length);
  }

  // 3) 충돌 감지
  let conflict = "";
  const isFormalTpo = FORMAL_TPOS.has(tpo);

  // formal + sport 조합 (가장 심각)
  if (counts.formal > 0 && counts.sport > 0) {
    conflict = "포멀 아이템과 스포츠 아이템이 함께 포함됨";
  }
  // 포멀도 편차 > 1.5 (셔츠 4.0 + 조거팬츠 1.5 같은 극단 조합)
  else if (formalityStd > 1.5) {
    conflict = "아이템 간 격식 수준 차이가 큼";
  }
  // formal TPO에서 casual 비율 > 40%
  else if (isFormalTpo && counts.casual / total > 0.4) {
    conflict = "격식 있는 상황에 캐주얼 비율이 높음";
  }
  // formal TPO에서 포멀도 편차 > 1.0
  else if (isFormalTpo && formalityStd > 1.0) {
    conflict = "격식 있는 상황에 포멀도가 일관되지 않음";
  }
  // sport TPO가 아닌데 sport 비율 > 50%
  else if (tpo !== "workout" && counts.sport / total > 0.5) {
    conflict = "스포츠 아이템 비율이 과도함";
  }

  const pass = ratio >= 0.5 && conflict === "";

  return { pass, dominant, ratio, conflict, formalityStd };
}

// ── TPO별 스타일 재해석 맵 ──
// 사용자가 선택한 스타일이 TPO 맥락에서 실제로 의미하는 style_tag 후보
const TPO_STYLE_REINTERPRET: Record<string, Record<string, string[]>> = {
  interview: {
    casual: ["minimal", "feminine"],   // 딱딱하지 않은 면접룩
    street: ["minimal"],               // 면접에서 스트릿 = 깔끔한 미니멀
    sporty: ["minimal"],
    dandy: ["formal", "minimal"],
  },
  event: {
    casual: ["feminine", "minimal"],   // 격식 낮은 행사룩
    street: ["minimal"],
    sporty: ["feminine"],
  },
  commute: {
    sporty: ["casual", "minimal"],     // 스포티 출근 = 편한 캐주얼
    street: ["casual"],
  },
  workout: {
    formal: ["sporty"],                // 운동에서 포멀 = 스포티
    minimal: ["sporty", "casual"],
  },
};

// 전역 유사 스타일 (TPO 재해석에 없을 때 fallback)
const STYLE_SIMILAR: Record<string, string[]> = {
  casual: ["minimal", "street"], formal: ["minimal", "classic"],
  minimal: ["formal", "casual"], feminine: ["elegant", "romantic"],
  sporty: ["casual", "street"], classic: ["formal", "minimal"],
  street: ["casual", "sporty"], dandy: ["formal", "classic"],
  romantic: ["feminine", "elegant"], elegant: ["feminine", "formal"],
};

// TPO 맥락에서 차이 설명 문구
const TPO_STYLE_EXPLAIN: Record<string, Record<string, string>> = {
  interview: {
    casual: "면접에서는 캐주얼 대신 깔끔한 미니멀 스타일을 추천해요",
    street: "면접 상황에 맞게 격식을 유지하면서 깔끔하게 구성했어요",
    sporty: "면접에는 스포티 대신 단정한 스타일을 추천해요",
  },
  event: {
    casual: "행사에서는 격식을 유지하면서 부드러운 느낌으로 구성했어요",
    street: "행사 상황에 맞게 세련된 스타일로 추천해요",
  },
  commute: {
    sporty: "출근에는 스포티 대신 편안한 캐주얼로 구성했어요",
  },
};

/** 사용자 style_moods 기반 soft score 계산 (TPO 재해석 적용) */
function calcMoodScore(outfit: FeedOutfit, userMoods: string[], tpo: string): number {
  if (userMoods.length === 0) return 0;
  let score = 0;
  const tag = outfit.tags ?? [];
  const moods = tag.filter(t => !TPO_SET.has(t) && !SEASON_SET.has(t));
  const styleTag = (outfit as Record<string, unknown>).style_tag as string | undefined;
  const reinterpret = TPO_STYLE_REINTERPRET[tpo] ?? {};

  for (const mood of userMoods) {
    // 1) designed_moods 직접 일치
    if (moods.includes(mood)) { score += 2; continue; }
    // 2) style_tag 직접 일치
    if (styleTag === mood) { score += 2; continue; }
    // 3) TPO 재해석 매칭 (면접+casual → minimal/feminine)
    const reinterpreted = reinterpret[mood];
    if (reinterpreted && styleTag && reinterpreted.includes(styleTag)) { score += 2; continue; }
    // 4) 전역 유사 스타일
    if (styleTag && (STYLE_SIMILAR[mood] ?? []).includes(styleTag)) { score += 1; }
  }
  return score;
}

/** TPO 맥락에서 스타일 재해석 설명이 필요한지 판단 */
export function getStyleExplanation(userMoods: string[], tpo: string): string {
  for (const mood of userMoods) {
    const msg = TPO_STYLE_EXPLAIN[tpo]?.[mood];
    if (msg) return msg;
  }
  return "";
}

/** API 결과를 스타일 일관성 + 사용자 무드 기반으로 후처리 정렬 */
export function applyStyleFilter(outfits: FeedOutfit[], tpo: string, userMoods: string[] = []): FeedOutfit[] {
  // 1) 스타일 일관성 분류
  const scored: { outfit: FeedOutfit; consistency: boolean; moodScore: number }[] = [];
  for (const o of outfits) {
    const check = checkStyleConsistency(o, tpo);
    const moodScore = calcMoodScore(o, userMoods, tpo);
    scored.push({ outfit: o, consistency: check.pass, moodScore });
  }

  // 2) 정렬: 일관성 통과 + 무드 점수 높은 순
  scored.sort((a, b) => {
    if (a.consistency !== b.consistency) return a.consistency ? -1 : 1;
    return b.moodScore - a.moodScore;
  });

  return scored.map(s => s.outfit);
}
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
    result.push({
      outfit: pick2.outfit, topAxis: pick2.axis,
      label: AXIS_LABELS[pick2.axis] ?? pick2.axis,
      diffDesc: AXIS_DESC[pick2.axis] ?? "", rank: 2,
    });
    usedAxes.add(pick2.axis);
    usedIds.add(pick2.outfit.outfit_id);
    usedCombos.add(pick2.combo);
  }

  const remaining = pool.filter(c => !usedIds.has(c.outfit.outfit_id));
  const pick3combo = remaining.find(c => !usedCombos.has(c.combo) && !usedAxes.has(c.axis));
  const pick3any = remaining.find(c => !usedCombos.has(c.combo));
  const pick3 = pick3combo ?? pick3any ?? remaining[0];

  if (pick3) {
    result.push({
      outfit: pick3.outfit, topAxis: pick3.axis,
      label: AXIS_LABELS[pick3.axis] ?? pick3.axis,
      diffDesc: AXIS_DESC[pick3.axis] ?? "", rank: 3,
    });
  }

  return result;
}

export { AXIS_LABELS, AXIS_DESC, AXIS_WEIGHTS, getStyleExplanation };
