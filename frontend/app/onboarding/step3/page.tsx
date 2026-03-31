"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { updateOnboarding } from "@/lib/onboarding-store";

const TPO_OPTIONS = [
  { id: "commute", label: "출근" },
  { id: "interview", label: "면접" },
  { id: "campus", label: "캠퍼스" },
  { id: "date", label: "데이트" },
  { id: "weekend", label: "주말" },
  { id: "travel", label: "여행" },
  { id: "event", label: "행사" },
  { id: "workout", label: "운동" },
];

interface MoodOption {
  id: string;
  label: string;
}

const MOOD_BY_GENDER: Record<string, MoodOption[]> = {
  female: [
    { id: "minimal", label: "미니멀" },
    { id: "classic", label: "클래식" },
    { id: "casual", label: "캐주얼" },
    { id: "lovely", label: "러블리" },
    { id: "street", label: "스트릿" },
    { id: "editorial", label: "에디토리얼" },
  ],
  male: [
    { id: "minimal", label: "미니멀" },
    { id: "classic", label: "클래식" },
    { id: "casual", label: "캐주얼" },
    { id: "dandy", label: "댄디" },
    { id: "street", label: "스트릿" },
    { id: "amekaji", label: "아메카지" },
  ],
};

const MAX_TPO = 3;
const MAX_MOOD = 5;

export default function Step3Page() {
  const router = useRouter();
  const [selectedTpo, setSelectedTpo] = useState<Set<string>>(new Set());
  const [selectedMood, setSelectedMood] = useState<Set<string>>(new Set());

  // TODO: read gender from onboarding state; default to female
  const gender = "female";
  const moods = MOOD_BY_GENDER[gender];

  const toggleTpo = (id: string) => {
    setSelectedTpo((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else if (next.size < MAX_TPO) {
        next.add(id);
      }
      return next;
    });
  };

  const toggleMood = (id: string) => {
    setSelectedMood((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else if (next.size < MAX_MOOD) {
        next.add(id);
      }
      return next;
    });
  };

  const canProceed = selectedTpo.size > 0;

  const handleNext = () => {
    if (canProceed) {
      updateOnboarding({
        tpo_list: Array.from(selectedTpo),
        style_moods: Array.from(selectedMood),
      });
      router.push("/onboarding/step4");
    }
  };

  return (
    <div className="flex flex-col h-full px-md pt-lg pb-md">
      {/* Headline */}
      <h2 className="text-center text-primary" style={{ fontSize: "24px" }}>
        어떤 상황의 코디를 찾으세요?
      </h2>

      {/* TPO selection */}
      <section className="mt-xl">
        <p className="text-text-secondary mb-sm" style={{ fontSize: "13px" }}>
          TPO 선택 (최대 {MAX_TPO}개) · {selectedTpo.size}/{MAX_TPO}
        </p>
        <div className="flex flex-wrap gap-sm">
          {TPO_OPTIONS.map((tpo) => {
            const isActive = selectedTpo.has(tpo.id);
            return (
              <motion.button
                key={tpo.id}
                onClick={() => toggleTpo(tpo.id)}
                whileTap={{ scale: 0.95 }}
                className="px-md py-sm rounded-full font-medium"
                style={{
                  fontSize: "14px",
                  backgroundColor: isActive ? "#964F4C" : "#FFFFFF",
                  color: isActive ? "#FFFFFF" : "#222222",
                  border: isActive
                    ? "1.5px solid #964F4C"
                    : "1.5px solid #E0DCD7",
                  transition: "background-color 0.2s, color 0.2s, border-color 0.2s",
                }}
              >
                {tpo.label}
              </motion.button>
            );
          })}
        </div>
      </section>

      {/* Mood selection */}
      <section className="mt-xl flex-1">
        <p className="text-text-secondary mb-xs" style={{ fontSize: "15px", fontWeight: 500, color: "#222222" }}>
          분위기도 골라보세요
        </p>
        <p className="text-text-secondary mb-sm" style={{ fontSize: "13px" }}>
          무드 선택 (최대 {MAX_MOOD}개) · {selectedMood.size}/{MAX_MOOD}
        </p>
        <div className="flex flex-wrap gap-x-lg gap-y-md">
          {moods.map((mood) => {
            const isActive = selectedMood.has(mood.id);
            return (
              <button
                key={mood.id}
                onClick={() => toggleMood(mood.id)}
                style={{
                  fontSize: "15px",
                  fontWeight: isActive ? 600 : 400,
                  color: "#222222",
                  textDecoration: "none",
                  borderBottom: isActive
                    ? "2px solid #964F4C"
                    : "2px solid transparent",
                  paddingBottom: 2,
                  transition: "font-weight 0.2s, border-color 0.2s",
                }}
              >
                {mood.label}
              </button>
            );
          })}
        </div>
      </section>

      {/* CTA */}
      <button
        onClick={handleNext}
        disabled={!canProceed}
        className="w-full rounded-xl text-white font-semibold mt-lg"
        style={{
          height: 56,
          fontSize: "16px",
          backgroundColor: canProceed ? "#964F4C" : "#E0DCD7",
          transition: "background-color 0.3s",
        }}
      >
        다음
      </button>
    </div>
  );
}
