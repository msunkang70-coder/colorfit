"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { updateOnboarding } from "@/lib/onboarding-store";

const GENDERS = [
  {
    id: "female",
    label: "Women",
    sub: "여성 스타일링",
    accent: "#C4726F",
  },
  {
    id: "male",
    label: "Men",
    sub: "남성 스타일링",
    accent: "#7FA3A3",
  },
] as const;

export default function Step1Page() {
  const router = useRouter();
  const [selected, setSelected] = useState<string | null>(null);

  const handleSelect = (id: string) => {
    setSelected(id);
    updateOnboarding({ gender: id });
  };

  return (
    <div className="ob-page">
      {/* BG — 웰컴과 동일 톤 유지 */}
      <div className="ob-bg ob-bg-step1" />
      <div className="ob-overlay" />

      {/* Content */}
      <div className="ob-content">
        {/* Headline */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <h1 style={{ fontFamily: "var(--font-display)", fontSize: "22px", fontWeight: 700, color: "#fff", lineHeight: 1.3 }}>
            나에게 맞는
            <br />스타일을 찾아볼까요?
          </h1>
          <p style={{ fontSize: "11px", color: "rgba(255,255,255,0.5)", marginTop: 6 }}>
            성별에 따라 맞춤 코디가 달라져요
          </p>
        </motion.div>

        {/* Cards — glassmorphism */}
        <div style={{ display: "flex", gap: 10 }}>
          {GENDERS.map((g, i) => {
            const on = selected === g.id;
            return (
              <motion.button
                key={g.id}
                initial={{ opacity: 0, y: 14 }}
                animate={{ opacity: 1, y: on ? -3 : 0, scale: on ? 1.02 : 1 }}
                transition={{ delay: 0.12 + i * 0.08, duration: 0.35 }}
                whileTap={{ scale: 0.96 }}
                onClick={() => handleSelect(g.id)}
                style={{
                  flex: 1,
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  borderRadius: 16,
                  padding: "18px 14px 16px",
                  minHeight: 160,
                  background: on
                    ? `linear-gradient(160deg, ${g.accent}30, ${g.accent}18)`
                    : "rgba(255,255,255,0.08)",
                  backdropFilter: "blur(12px)",
                  WebkitBackdropFilter: "blur(12px)",
                  border: on ? `2px solid ${g.accent}` : "1px solid rgba(255,255,255,0.12)",
                  boxShadow: on ? `0 8px 24px ${g.accent}30` : "none",
                  cursor: "pointer",
                }}
              >
                {/* 상단 */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ width: 24, height: 3, borderRadius: 2, backgroundColor: on ? g.accent : "rgba(255,255,255,0.2)" }} />
                  {on && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      style={{ width: 22, height: 22, borderRadius: 11, background: g.accent, display: "flex", alignItems: "center", justifyContent: "center" }}
                    >
                      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3"><polyline points="20 6 9 17 4 12" /></svg>
                    </motion.div>
                  )}
                </div>
                {/* 하단 */}
                <div style={{ marginTop: "auto" }}>
                  <span style={{ fontFamily: "var(--font-display)", fontSize: "24px", fontWeight: 700, color: on ? g.accent : "rgba(255,255,255,0.85)", display: "block" }}>
                    {g.label}
                  </span>
                  <span style={{ fontSize: "11px", fontWeight: 500, color: on ? g.accent : "rgba(255,255,255,0.45)", marginTop: 3, display: "block" }}>
                    {g.sub}
                  </span>
                </div>
              </motion.button>
            );
          })}
        </div>

        {/* CTA */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
          <button
            onClick={() => { if (selected) router.push("/onboarding/step2"); }}
            disabled={!selected}
            style={{
              width: "100%",
              padding: "13px 0",
              borderRadius: 14,
              fontSize: 14,
              fontWeight: 600,
              color: "#fff",
              background: selected
                ? "linear-gradient(135deg, #7A3E3C, #964F4C, #B5605D)"
                : "rgba(255,255,255,0.1)",
              border: selected ? "none" : "1px solid rgba(255,255,255,0.1)",
              boxShadow: selected ? "0 4px 16px rgba(150,79,76,0.3)" : "none",
              cursor: selected ? "pointer" : "default",
              transition: "all 0.2s",
            }}
          >
            시작하기
          </button>
          <button
            onClick={() => { updateOnboarding({ gender: "female" }); router.push("/onboarding/step2"); }}
            style={{ width: "100%", marginTop: 8, fontSize: 10, color: "rgba(255,255,255,0.25)", background: "none", border: "none", cursor: "pointer", textAlign: "center" }}
          >
            건너뛰기
          </button>
        </motion.div>
      </div>
    </div>
  );
}
