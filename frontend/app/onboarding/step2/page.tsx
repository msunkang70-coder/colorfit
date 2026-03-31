"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";

interface ToneChip {
  id: string;
  label: string;
  color: string;
}

interface Season {
  id: string;
  label: string;
  gradient: string;
  tones: ToneChip[];
}

const SEASONS: Season[] = [
  {
    id: "spring_warm",
    label: "봄 웜",
    gradient: "linear-gradient(to right, #F08080, #FFDAB9, #FFFFF0)",
    tones: [
      { id: "spring_warm_light", label: "라이트", color: "#FFDAB9" },
      { id: "spring_warm_bright", label: "브라이트", color: "#F08080" },
      { id: "spring_warm_mute", label: "뮤트", color: "#D4A589" },
    ],
  },
  {
    id: "summer_cool",
    label: "여름 쿨",
    gradient: "linear-gradient(to right, #B8A9D0, #87CEEB, #98E4D6)",
    tones: [
      { id: "summer_cool_light", label: "라이트", color: "#B8C9E8" },
      { id: "summer_cool_soft", label: "소프트", color: "#B8A9D0" },
      { id: "summer_cool_mute", label: "뮤트", color: "#A0B0B8" },
    ],
  },
  {
    id: "autumn_warm",
    label: "가을 웜",
    gradient: "linear-gradient(to right, #800020, #C66A4A, #C6A664)",
    tones: [
      { id: "autumn_warm_deep", label: "딥", color: "#800020" },
      { id: "autumn_warm_bright", label: "브라이트", color: "#C66A4A" },
      { id: "autumn_warm_mute", label: "뮤트", color: "#A68B6B" },
    ],
  },
  {
    id: "winter_cool",
    label: "겨울 쿨",
    gradient: "linear-gradient(to right, #1A1A1A, #4169E1, #FFB6C1)",
    tones: [
      { id: "winter_cool_deep", label: "딥", color: "#1A1A2E" },
      { id: "winter_cool_bright", label: "브라이트", color: "#4169E1" },
      { id: "winter_cool_light", label: "라이트", color: "#E8D0E0" },
    ],
  },
];

const UNDERTONE_OPTIONS = [
  { id: "warm", label: "따뜻한 톤 (노란/복숭아 빛)" },
  { id: "cool", label: "차가운 톤 (핑크/올리브 빛)" },
  { id: "neutral", label: "잘 모르겠어요" },
];

const BEST_COLOR_OPTIONS = [
  { id: "warm_vivid", label: "코랄, 피치 같은 따뜻하고 밝은 색", season: "spring_warm" },
  { id: "cool_soft", label: "라벤더, 스카이블루 같은 부드러운 색", season: "summer_cool" },
  { id: "warm_deep", label: "테라코타, 버건디 같은 깊은 색", season: "autumn_warm" },
  { id: "cool_vivid", label: "로열블루, 와인 같은 선명한 색", season: "winter_cool" },
];

export default function Step2Page() {
  const router = useRouter();
  const [selectedSeason, setSelectedSeason] = useState<string | null>(null);
  const [selectedTone, setSelectedTone] = useState<string | null>(null);
  const [showBottomSheet, setShowBottomSheet] = useState(false);
  const [undertone, setUndertone] = useState<string | null>(null);
  const [bestColor, setBestColor] = useState<string | null>(null);

  const handleSeasonTap = (seasonId: string) => {
    if (selectedSeason === seasonId) {
      setSelectedSeason(null);
      setSelectedTone(null);
    } else {
      setSelectedSeason(seasonId);
      setSelectedTone(null);
    }
  };

  const handleToneTap = (toneId: string) => {
    setSelectedTone(toneId);
  };

  const handleNext = () => {
    if (selectedTone) {
      router.push("/onboarding/step3");
    }
  };

  const handleQuickDiagnosis = () => {
    if (!undertone || !bestColor) return;

    const match = BEST_COLOR_OPTIONS.find((o) => o.id === bestColor);
    if (match) {
      const season = SEASONS.find((s) => s.id === match.season);
      if (season) {
        setSelectedSeason(season.id);
        setSelectedTone(season.tones[0].id);
      }
    }
    setShowBottomSheet(false);
  };

  return (
    <div className="flex flex-col h-full px-md pt-lg pb-md">
      {/* Headline */}
      <h2 className="text-center text-primary" style={{ fontSize: "24px" }}>
        어떤 컬러가 잘 어울리세요?
      </h2>

      {/* Season strips */}
      <div className="flex flex-col gap-lg mt-xl flex-1">
        {SEASONS.map((season) => {
          const isSelected = selectedSeason === season.id;
          const isDimmed = selectedSeason !== null && !isSelected;

          return (
            <div key={season.id}>
              {/* Season label */}
              <p
                className="mb-xs"
                style={{
                  fontSize: "13px",
                  fontWeight: 500,
                  color: isDimmed ? "#B5AFA6" : "#8C8578",
                  transition: "color 0.3s",
                }}
              >
                {season.label}
              </p>

              {/* Gradient strip */}
              <motion.button
                onClick={() => handleSeasonTap(season.id)}
                animate={{
                  height: isSelected ? 64 : 48,
                  opacity: isDimmed ? 0.4 : 1,
                }}
                transition={{ type: "spring", stiffness: 300, damping: 30 }}
                className="w-full rounded-full"
                style={{ background: season.gradient }}
              />

              {/* Tone chips */}
              <AnimatePresence>
                {isSelected && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.25, ease: "easeOut" as const }}
                    className="flex gap-md justify-center mt-sm overflow-hidden"
                  >
                    {season.tones.map((tone) => (
                      <button
                        key={tone.id}
                        onClick={() => handleToneTap(tone.id)}
                        className="flex flex-col items-center gap-[4px]"
                      >
                        <div
                          className="rounded-full"
                          style={{
                            width: 32,
                            height: 32,
                            backgroundColor: tone.color,
                            border:
                              selectedTone === tone.id
                                ? "2.5px solid #964F4C"
                                : "2px solid #E5E1DA",
                            transition: "border 0.2s",
                          }}
                        />
                        <span
                          style={{
                            fontSize: "11px",
                            color:
                              selectedTone === tone.id
                                ? "#964F4C"
                                : "#8C8578",
                          }}
                        >
                          {tone.label}
                        </span>
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </div>

      {/* Bottom area */}
      <div className="mt-lg flex flex-col items-center gap-md">
        {/* "I don't know" link */}
        <button
          onClick={() => setShowBottomSheet(true)}
          className="text-text-secondary underline"
          style={{ fontSize: "14px" }}
        >
          잘 모르겠어요
        </button>

        {/* CTA */}
        <button
          onClick={handleNext}
          disabled={!selectedTone}
          className="w-full rounded-xl text-white font-semibold"
          style={{
            height: 56,
            fontSize: "16px",
            backgroundColor: selectedTone ? "#964F4C" : "#E0DCD7",
            transition: "background-color 0.3s",
          }}
        >
          다음
        </button>
      </div>

      {/* Bottom sheet */}
      <AnimatePresence>
        {showBottomSheet && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.4 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowBottomSheet(false)}
              className="fixed inset-0 bg-black z-40"
            />

            {/* Sheet */}
            <motion.div
              initial={{ y: "100%" }}
              animate={{ y: 0 }}
              exit={{ y: "100%" }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              className="fixed bottom-0 left-0 right-0 z-50 bg-bg rounded-t-lg px-lg pt-lg pb-xl"
              style={{ maxWidth: 768, margin: "0 auto" }}
            >
              <h3 className="text-center mb-lg" style={{ fontSize: "18px" }}>
                간이 퍼스널컬러 진단
              </h3>

              {/* Q1: Undertone */}
              <p
                className="mb-sm font-medium"
                style={{ fontSize: "15px" }}
              >
                피부 언더톤이 어떤 편인가요?
              </p>
              <div className="flex flex-col gap-sm mb-lg">
                {UNDERTONE_OPTIONS.map((opt) => (
                  <button
                    key={opt.id}
                    onClick={() => setUndertone(opt.id)}
                    className="w-full text-left px-md py-sm rounded-md"
                    style={{
                      fontSize: "14px",
                      border:
                        undertone === opt.id
                          ? "1.5px solid #964F4C"
                          : "1.5px solid #E5E1DA",
                      backgroundColor:
                        undertone === opt.id ? "#F5EDEC" : "#FFFFFF",
                      transition: "border-color 0.2s, background-color 0.2s",
                    }}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>

              {/* Q2: Best color */}
              <p
                className="mb-sm font-medium"
                style={{ fontSize: "15px" }}
              >
                어울린다는 말을 가장 많이 들은 색은?
              </p>
              <div className="flex flex-col gap-sm mb-lg">
                {BEST_COLOR_OPTIONS.map((opt) => (
                  <button
                    key={opt.id}
                    onClick={() => setBestColor(opt.id)}
                    className="w-full text-left px-md py-sm rounded-md"
                    style={{
                      fontSize: "14px",
                      border:
                        bestColor === opt.id
                          ? "1.5px solid #964F4C"
                          : "1.5px solid #E5E1DA",
                      backgroundColor:
                        bestColor === opt.id ? "#F5EDEC" : "#FFFFFF",
                      transition: "border-color 0.2s, background-color 0.2s",
                    }}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>

              {/* Submit */}
              <button
                onClick={handleQuickDiagnosis}
                disabled={!undertone || !bestColor}
                className="w-full rounded-xl text-white font-semibold"
                style={{
                  height: 48,
                  fontSize: "15px",
                  backgroundColor:
                    undertone && bestColor ? "#964F4C" : "#E0DCD7",
                  transition: "background-color 0.3s",
                }}
              >
                결과 확인
              </button>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
