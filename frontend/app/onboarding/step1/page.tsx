"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";

const GENDERS = [
  { id: "female", label: "여성", letter: "W" },
  { id: "male", label: "남성", letter: "M" },
] as const;

const cardVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.15, duration: 0.4, ease: "easeOut" as const },
  }),
};

export default function Step1Page() {
  const router = useRouter();
  const [selected, setSelected] = useState<string | null>(null);

  const handleSelect = (genderId: string) => {
    if (selected) return;
    setSelected(genderId);
    setTimeout(() => {
      router.push("/onboarding/step2");
    }, 300);
  };

  const handleSkip = () => {
    if (selected) return;
    handleSelect("female");
  };

  return (
    <div className="flex flex-col items-center justify-center h-full px-md">
      {/* Headline */}
      <h1
        className="text-center text-primary"
        style={{ fontSize: "28px", lineHeight: 1.2 }}
      >
        나에 대해 알려주세요
      </h1>

      {/* Subtext */}
      <p
        className="mt-sm text-center text-text-secondary"
        style={{ fontSize: "15px" }}
      >
        맞춤 코디를 위해 필요해요
      </p>

      {/* Gender cards */}
      <div className="flex gap-md mt-2xl w-full justify-center">
        {GENDERS.map((gender, i) => (
          <motion.button
            key={gender.id}
            custom={i}
            variants={cardVariants}
            initial="hidden"
            animate="visible"
            whileTap={{ scale: 1.05 }}
            onClick={() => handleSelect(gender.id)}
            className="flex flex-col items-center justify-center rounded-2xl"
            style={{
              width: "45%",
              aspectRatio: "3 / 4",
              backgroundColor: "#FFFFFF",
              border:
                selected === gender.id
                  ? "2px solid #964F4C"
                  : "2px solid transparent",
              transform: selected === gender.id ? "scale(1.05)" : undefined,
              transition: "border-color 0.2s, transform 0.2s",
            }}
          >
            <span
              style={{
                fontFamily: '"Nanum Myeongjo", serif',
                fontSize: "48px",
                fontWeight: 700,
                color: "#222222",
              }}
            >
              {gender.letter}
            </span>
            <span
              className="mt-sm text-text-secondary"
              style={{ fontSize: "14px" }}
            >
              {gender.label}
            </span>
          </motion.button>
        ))}
      </div>

      {/* Skip link */}
      <button
        onClick={handleSkip}
        className="mt-2xl text-text-secondary underline"
        style={{ fontSize: "14px" }}
      >
        건너뛰기
      </button>
    </div>
  );
}
