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
