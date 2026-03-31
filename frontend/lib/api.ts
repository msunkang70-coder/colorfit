/**
 * API 클라이언트 — 백엔드 엔드포인트 호출 유틸리티.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function postOnboarding(body: {
  gender: string;
  tone_id: string;
  tpo_list: string[];
  style_moods: string[];
  budget_min: number;
  budget_max: number;
  style_seed_choices: { round: number; image_id: string }[];
}): Promise<{ user_id: string }> {
  const res = await fetch(`${API_BASE}/api/onboarding`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    throw new Error(`Onboarding API failed: ${res.status}`);
  }

  return res.json();
}

export async function postReaction(body: {
  user_id: string;
  outfit_id: string;
  reaction_type: "save" | "dislike";
}): Promise<void> {
  await fetch(`${API_BASE}/api/reaction`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

// ── Metrics ──

const STORAGE_KEY = "colorfit_metrics_queue";
const MAX_QUEUE = 100;

export interface MetricsPayload {
  session_id: string;
  outfit_id: string;
  page_view_ts: string;
  decision_click_ts: string;
  ttd_ms: number;
  cta_clicked: boolean;
  trust_score: number;
  confidence: string;
  tone_id: string;
  tpo: string;
  timestamp: string;
  // v3 Explore Mode 필드
  expanded: boolean;
  expand_level: number;
  selected_rank: number;
}

function saveToQueue(entry: MetricsPayload): void {
  try {
    const queue: MetricsPayload[] = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "[]");
    queue.push(entry);
    // FIFO: 최대 100개 유지
    const trimmed = queue.length > MAX_QUEUE ? queue.slice(queue.length - MAX_QUEUE) : queue;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
  } catch {
    // localStorage 접근 불가 (private browsing 등) — silent fail
  }
}

export function getMetricsQueue(): MetricsPayload[] {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "[]");
  } catch {
    return [];
  }
}

export function clearMetricsQueue(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // silent
  }
}

export function exportMetricsCsv(): string {
  const queue = getMetricsQueue();
  const header = "timestamp,ttd_ms,trust_score,confidence,cta_clicked,expanded,expand_level,selected_rank";
  const rows = queue.map((m) =>
    [m.timestamp, m.ttd_ms, m.trust_score, m.confidence, m.cta_clicked, m.expanded ?? false, m.expand_level ?? 0, m.selected_rank ?? 1].join(",")
  );
  return [header, ...rows].join("\n");
}

/**
 * 측정 데이터 전송. 완전 비동기 — 절대 호출자를 block하지 않는다.
 * 우선순위: sendBeacon > fetch(keepalive) > localStorage only
 */
export function postMetrics(body: MetricsPayload): void {
  const json = JSON.stringify(body);
  const url = `${API_BASE}/api/metrics`;

  // 항상 localStorage에 저장 (누락 방지)
  saveToQueue(body);

  // 1순위: sendBeacon (페이지 언로드에도 안전)
  if (typeof navigator !== "undefined" && navigator.sendBeacon) {
    const blob = new Blob([json], { type: "application/json" });
    const sent = navigator.sendBeacon(url, blob);
    if (sent) return;
  }

  // 2순위: fetch keepalive (sendBeacon 실패 시)
  try {
    fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: json,
      keepalive: true,
    }).catch(() => {
      // 서버 down — localStorage에 이미 저장됨
    });
  } catch {
    // fetch 자체 에러 — localStorage에 이미 저장됨
  }
}
