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
    gradient: "linear-gradient(160deg, #F5EDEC 0%, #EDE3E1 100%)",
    accentColor: "#964F4C",
  },
  {
    id: "male",
    label: "Men",
    sub: "남성 스타일링",
    gradient: "linear-gradient(160deg, #EDF0F0 0%, #E3E8E8 100%)",
    accentColor: "#4F6B6B",
  },
] as const;

export default function Step1Page() {
  const router = useRouter();
  const [selected, setSelected] = useState<string | null>(null);

  const handleSelect = (id: string) => {
    setSelected(id);
    updateOnboarding({ gender: id });
  };

  const handleNext = () => {
    if (!selected) return;
    router.push("/onboarding/step2");
  };

  return (
    <div className="flex flex-col min-h-full px-[24px] pb-[28px]">
      {/* Spacer */}
      <div style={{ height: "6vh" }} />

      {/* Headline */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1 style={{ fontFamily: "var(--font-display)", fontSize: "28px", fontWeight: 700, lineHeight: 1.25, color: "#222" }}>
          나에게 맞는
          <br />
          스타일을 찾아볼까요?
        </h1>
        <p style={{ fontSize: "14px", color: "#8C8578", marginTop: 10, lineHeight: 1.5 }}>
          퍼스널컬러와 상황에 딱 맞는 코디를 추천해드려요
        </p>
      </motion.div>

      {/* Cards */}
      <div className="flex gap-[12px] mt-[32px] flex-1">
        {GENDERS.map((g, i) => {
          const isSelected = selected === g.id;
          return (
            <motion.button
              key={g.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.25 + i * 0.1, duration: 0.4 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => handleSelect(g.id)}
              className="flex-1 flex flex-col justify-between rounded-2xl overflow-hidden"
              style={{
                background: isSelected ? g.gradient : "#FFFFFF",
                border: isSelected ? `2.5px solid ${g.accentColor}` : "1px solid #E5E1DA",
                padding: "24px 16px 20px",
                minHeight: 220,
                transition: "all 0.3s ease",
                boxShadow: isSelected ? `0 8px 28px ${g.accentColor}20` : "0 2px 8px rgba(0,0,0,0.03)",
              }}
            >
              {/* Top — decorative line */}
              <div
                style={{
                  width: 32,
                  height: 3,
                  borderRadius: 2,
                  backgroundColor: isSelected ? g.accentColor : "#E5E1DA",
                  transition: "background-color 0.3s",
                }}
              />

              {/* Bottom — text */}
              <div>
                <span
                  style={{
                    fontFamily: "var(--font-display)",
                    fontSize: "26px",
                    fontWeight: 700,
                    color: isSelected ? g.accentColor : "#222",
                    letterSpacing: "-0.3px",
                    display: "block",
                    transition: "color 0.3s",
                  }}
                >
                  {g.label}
                </span>
                <span
                  style={{
                    fontSize: "12px",
                    fontWeight: 500,
                    color: isSelected ? g.accentColor : "#8C8578",
                    marginTop: 4,
                    display: "block",
                    transition: "color 0.3s",
                  }}
                >
                  {g.sub}
                </span>
              </div>
            </motion.button>
          );
        })}
      </div>

      {/* Bottom */}
      <div className="mt-[24px]">
        <motion.button
          whileTap={selected ? { scale: 0.98 } : {}}
          onClick={handleNext}
          disabled={!selected}
          className="w-full cta-primary"
        >
          시작하기
        </motion.button>

        <button
          onClick={() => { updateOnboarding({ gender: "female" }); router.push("/onboarding/step2"); }}
          className="w-full mt-[10px] text-center"
          style={{ fontSize: "12px", color: "#B5AFA6", background: "none", border: "none", cursor: "pointer" }}
        >
          건너뛰기
        </button>
      </div>
    </div>
  );
}
