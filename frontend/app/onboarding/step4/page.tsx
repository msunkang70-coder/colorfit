"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion, useAnimation } from "framer-motion";
import { updateOnboarding } from "@/lib/onboarding-store";

const MIN_BUDGET = 0;
const MAX_BUDGET = 300000;
const STEP = 10000;

const PRESETS = [
  { label: "~3만", min: 0, max: 30000 },
  { label: "3~7만", min: 30000, max: 70000 },
  { label: "7~15만", min: 70000, max: 150000 },
  { label: "15만~", min: 150000, max: 300000 },
];

function formatKRW(value: number): string {
  return `₩${value.toLocaleString("ko-KR")}`;
}

function clamp(val: number, min: number, max: number) {
  return Math.min(Math.max(val, min), max);
}

function snapToStep(val: number) {
  return Math.round(val / STEP) * STEP;
}

export default function Step4Page() {
  const router = useRouter();
  const ctaControls = useAnimation();
  const [budgetMin, setBudgetMin] = useState(30000);
  const [budgetMax, setBudgetMax] = useState(100000);
  const [dragging, setDragging] = useState<"min" | "max" | null>(null);
  const trackRef = useRef<HTMLDivElement>(null);
  const hasPulsed = useRef(false);

  const pctMin = ((budgetMin - MIN_BUDGET) / (MAX_BUDGET - MIN_BUDGET)) * 100;
  const pctMax = ((budgetMax - MIN_BUDGET) / (MAX_BUDGET - MIN_BUDGET)) * 100;

  const getValueFromX = useCallback((clientX: number) => {
    const track = trackRef.current;
    if (!track) return 0;
    const rect = track.getBoundingClientRect();
    const pct = (clientX - rect.left) / rect.width;
    const raw = MIN_BUDGET + pct * (MAX_BUDGET - MIN_BUDGET);
    return snapToStep(clamp(raw, MIN_BUDGET, MAX_BUDGET));
  }, []);

  const handlePointerDown = (thumb: "min" | "max") => (e: React.PointerEvent) => {
    e.preventDefault();
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
    setDragging(thumb);
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!dragging) return;
    const val = getValueFromX(e.clientX);
    if (dragging === "min") {
      setBudgetMin(Math.min(val, budgetMax - STEP));
    } else {
      setBudgetMax(Math.max(val, budgetMin + STEP));
    }
  };

  const handlePointerUp = () => {
    setDragging(null);
  };

  const applyPreset = (preset: { min: number; max: number }) => {
    setBudgetMin(preset.min);
    setBudgetMax(preset.max);
  };

  // Pulse CTA once when budget is set
  useEffect(() => {
    if (!hasPulsed.current && budgetMin !== 30000 || budgetMax !== 100000) {
      hasPulsed.current = true;
      ctaControls.start({
        scale: [1, 1.03, 1],
        transition: { duration: 0.4, ease: "easeInOut" },
      });
    }
  }, [budgetMin, budgetMax, ctaControls]);

  const handleNext = () => {
    updateOnboarding({ budget_min: budgetMin, budget_max: budgetMax });
    router.push("/onboarding/step5");
  };

  return (
    <div className="flex flex-col h-full px-md pt-lg pb-md">
      {/* Headline */}
      <h2 className="text-center text-primary" style={{ fontSize: "24px" }}>
        예산 범위를 알려주세요
      </h2>

      {/* Budget display */}
      <p
        className="text-center mt-xl font-bold"
        style={{ fontSize: "18px" }}
      >
        {formatKRW(budgetMin)} ~ {formatKRW(budgetMax)}
      </p>

      {/* Dual-thumb range slider */}
      <div
        className="relative mt-xl mx-sm"
        style={{ height: 40 }}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
      >
        {/* Track */}
        <div
          ref={trackRef}
          className="absolute top-1/2 left-0 right-0 -translate-y-1/2 rounded-full"
          style={{ height: 4, backgroundColor: "#E0DCD7" }}
        />

        {/* Active range */}
        <div
          className="absolute top-1/2 -translate-y-1/2 rounded-full"
          style={{
            height: 4,
            left: `${pctMin}%`,
            right: `${100 - pctMax}%`,
            backgroundColor: "#964F4C",
          }}
        />

        {/* Min thumb */}
        <div
          onPointerDown={handlePointerDown("min")}
          className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 cursor-grab active:cursor-grabbing touch-none"
          style={{
            left: `${pctMin}%`,
            width: 24,
            height: 24,
            borderRadius: "50%",
            backgroundColor: "#FFFFFF",
            border: "2px solid #964F4C",
            boxShadow: "0 1px 3px rgba(0,0,0,0.12)",
          }}
        />

        {/* Max thumb */}
        <div
          onPointerDown={handlePointerDown("max")}
          className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 cursor-grab active:cursor-grabbing touch-none"
          style={{
            left: `${pctMax}%`,
            width: 24,
            height: 24,
            borderRadius: "50%",
            backgroundColor: "#FFFFFF",
            border: "2px solid #964F4C",
            boxShadow: "0 1px 3px rgba(0,0,0,0.12)",
          }}
        />
      </div>

      {/* Scale labels */}
      <div className="flex justify-between mx-sm mt-xs">
        <span className="text-text-tertiary" style={{ fontSize: "11px" }}>₩0</span>
        <span className="text-text-tertiary" style={{ fontSize: "11px" }}>₩300,000</span>
      </div>

      {/* Quick presets */}
      <div className="flex gap-sm mt-xl justify-center">
        {PRESETS.map((preset) => {
          const isActive =
            budgetMin === preset.min && budgetMax === preset.max;
          return (
            <button
              key={preset.label}
              onClick={() => applyPreset(preset)}
              className="px-md py-xs rounded-full"
              style={{
                fontSize: "13px",
                fontWeight: 500,
                backgroundColor: isActive ? "#964F4C" : "#FFFFFF",
                color: isActive ? "#FFFFFF" : "#222222",
                border: isActive
                  ? "1.5px solid #964F4C"
                  : "1.5px solid #E0DCD7",
                transition: "background-color 0.2s, color 0.2s, border-color 0.2s",
              }}
            >
              {preset.label}
            </button>
          );
        })}
      </div>

      {/* Spacer */}
      <div className="flex-1" />

      {/* CTA */}
      <motion.button
        animate={ctaControls}
        onClick={handleNext}
        className="w-full rounded-xl text-white font-semibold"
        style={{
          height: 56,
          fontSize: "16px",
          backgroundColor: "#964F4C",
        }}
      >
        추천 코디 보러가기
      </motion.button>
    </div>
  );
}
