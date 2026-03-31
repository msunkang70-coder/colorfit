/**
 * 온보딩 5 Step 상태를 localStorage에 영속 저장한다.
 * 새로고침/페이지 이동 후에도 프로필 유지.
 */

export interface StyleSeedChoice {
  round: number;
  image_id: string;
}

export interface OnboardingData {
  gender: string;
  tone_id: string;
  tpo_list: string[];
  style_moods: string[];
  budget_min: number;
  budget_max: number;
  style_seed_choices: StyleSeedChoice[];
}

const STORAGE_KEY = "colorfit_onboarding";

const DEFAULT_DATA: OnboardingData = {
  gender: "female",
  tone_id: "",
  tpo_list: [],
  style_moods: [],
  budget_min: 30000,
  budget_max: 100000,
  style_seed_choices: [],
};

function load(): OnboardingData {
  if (typeof window === "undefined") return { ...DEFAULT_DATA };
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return { ...DEFAULT_DATA, ...JSON.parse(raw) };
  } catch {
    // SSR or parse error
  }
  return { ...DEFAULT_DATA };
}

function save(data: OnboardingData): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch {
    // quota exceeded 등 무시
  }
}

export function getOnboardingData(): OnboardingData {
  return load();
}

export function updateOnboarding(partial: Partial<OnboardingData>): void {
  const current = load();
  const updated = { ...current, ...partial };
  save(updated);
}

export function resetOnboarding(): void {
  save({ ...DEFAULT_DATA });
}
