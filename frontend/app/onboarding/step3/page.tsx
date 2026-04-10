"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { getOnboardingData, updateOnboarding } from "@/lib/onboarding-store";

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

  const [gender, setGender] = useState("female");
  useEffect(() => {
    const data = getOnboardingData();
    if (data.gender) setGender(data.gender);
  }, []);
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
    <div className="ob-page">
      <div className={`ob-bg ${gender === "male" ? "ob-bg-step3-m" : "ob-bg-step3-f"}`} />
      <div className="ob-overlay" />
      <div className="ob-content">
      <h2 style={{ fontFamily: "var(--font-display)", fontSize: "20px", fontWeight: 700, color: "#fff", marginTop: 4 }}>
        어떤 상황의 코디를 찾으세요?
      </h2>

      {/* TPO selection */}
      <section style={{ marginTop: 16 }}>
        <p style={{ fontSize: "11px", color: "rgba(255,255,255,0.45)", marginBottom: 6 }}>
          TPO 선택 (최대 {MAX_TPO}개) · {selectedTpo.size}/{MAX_TPO}
        </p>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
          {TPO_OPTIONS.map((tpo) => {
            const isActive = selectedTpo.has(tpo.id);
            return (
              <motion.button
                key={tpo.id}
                onClick={() => toggleTpo(tpo.id)}
                whileTap={{ scale: 0.93 }}
                className={`glass-chip${isActive ? " on" : ""}`}
              >
                {tpo.label}
              </motion.button>
            );
          })}
        </div>
      </section>

      {/* Mood selection */}
      <section style={{ marginTop: 20, flex: 1 }}>
        <p style={{ fontSize: "14px", fontWeight: 600, color: "rgba(255,255,255,0.85)" }}>
          분위기도 골라보세요
        </p>
        <p style={{ fontSize: "11px", color: "rgba(255,255,255,0.4)", marginTop: 2, marginBottom: 8 }}>
          무드 선택 (최대 {MAX_MOOD}개) · {selectedMood.size}/{MAX_MOOD}
        </p>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "8px 20px" }}>
          {moods.map((mood) => {
            const isActive = selectedMood.has(mood.id);
            return (
              <button
                key={mood.id}
                onClick={() => toggleMood(mood.id)}
                style={{
                  fontSize: "14px",
                  fontWeight: isActive ? 600 : 400,
                  color: isActive ? "#fff" : "rgba(255,255,255,0.55)",
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
        className="cta-primary"
        style={{
          width: "100%",
          marginTop: 16,
          opacity: canProceed ? 1 : 0.5,
          fontSize: "14px",
        }}
      >
        다음
      </button>
      </div>{/* ob-content */}
    </div>
  );
}
