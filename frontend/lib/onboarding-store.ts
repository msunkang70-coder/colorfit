/**
 * 온보딩 5 Step 상태를 메모리에 누적한 뒤 마지막에 API로 전송한다.
 * 단순 모듈 스코프 싱글턴 — 외부 상태 라이브러리 불필요.
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

const DEFAULT_DATA: OnboardingData = {
  gender: "female",
  tone_id: "",
  tpo_list: [],
  style_moods: [],
  budget_min: 30000,
  budget_max: 100000,
  style_seed_choices: [],
};

let _data: OnboardingData = { ...DEFAULT_DATA };

export function getOnboardingData(): OnboardingData {
  return _data;
}

export function updateOnboarding(partial: Partial<OnboardingData>): void {
  _data = { ..._data, ...partial };
}

export function resetOnboarding(): void {
  _data = { ...DEFAULT_DATA };
}
