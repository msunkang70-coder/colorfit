"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { updateOnboarding, getOnboardingData } from "@/lib/onboarding-store";
import { postOnboarding } from "@/lib/api";

interface StyleImage {
  id: string;
  src: string;
  alt: string;
}

// Placeholder images per round — will be replaced with real style images
const ROUNDS: StyleImage[][] = [
  [
    { id: "r1-1", src: "/images/style/style_1.jpg", alt: "미니멀" },
    { id: "r1-2", src: "/images/style/style_2.jpg", alt: "캐주얼" },
    { id: "r1-3", src: "/images/style/style_3.jpg", alt: "스트릿" },
    { id: "r1-4", src: "/images/style/style_4.jpg", alt: "페미닌" },
  ],
  [
    { id: "r2-1", src: "/images/style/style_5.jpg", alt: "모던 오피스" },
    { id: "r2-2", src: "/images/style/style_6.jpg", alt: "빈티지" },
    { id: "r2-3", src: "/images/style/style_7.jpg", alt: "스포티" },
    { id: "r2-4", src: "/images/style/style_8.jpg", alt: "클래식" },
  ],
  [
    { id: "r3-1", src: "/images/style/style_9.jpg", alt: "오버사이즈" },
    { id: "r3-2", src: "/images/style/style_10.jpg", alt: "슬림핏" },
    { id: "r3-3", src: "/images/style/style_11.jpg", alt: "A라인" },
    { id: "r3-4", src: "/images/style/style_12.jpg", alt: "레이어드" },
  ],
  [
    { id: "r4-1", src: "/images/style/style_13.jpg", alt: "뉴트럴톤" },
    { id: "r4-2", src: "/images/style/style_14.jpg", alt: "비비드" },
    { id: "r4-3", src: "/images/style/style_15.jpg", alt: "파스텔" },
    { id: "r4-4", src: "/images/style/style_16.jpg", alt: "모노톤" },
  ],
];

const TOTAL_ROUNDS = ROUNDS.length;

export default function Step5Page() {
  const router = useRouter();
  const [round, setRound] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);
  const [showToast, setShowToast] = useState(false);
  const choices = useRef<{ round: number; image_id: string }[]>([]);

  const isLastRound = round === TOTAL_ROUNDS - 1;
  const images = ROUNDS[round];

  const submitOnboarding = async () => {
    updateOnboarding({ style_seed_choices: choices.current });
    const data = getOnboardingData();
    try {
      await postOnboarding(data);
    } catch {
      // API 실패해도 피드로 전환 (MVP graceful degradation)
    }
  };

  const goToFeed = async () => {
    setShowToast(true);
    await submitOnboarding();
    setTimeout(() => {
      router.push("/feed");
    }, 1200);
  };

  const advanceRound = () => {
    if (isLastRound) {
      goToFeed();
    } else {
      setSelected(null);
      setRound((r) => r + 1);
    }
  };

  const handleSelect = (imageId: string) => {
    if (selected) return;
    setSelected(imageId);
    choices.current.push({ round: round + 1, image_id: imageId });
    setTimeout(advanceRound, 500);
  };

  const handlePass = () => {
    if (selected) return;
    advanceRound();
  };

  const handleSkipAll = async () => {
    await submitOnboarding();
    router.push("/feed");
  };

  return (
    <div className="flex flex-col h-full px-md pt-lg pb-md">
      {/* Headline */}
      <h2 className="text-center text-primary" style={{ fontSize: "24px" }}>
        어떤 코디가 마음에 드세요?
      </h2>
      <p
        className="text-center mt-xs text-text-secondary"
        style={{ fontSize: "14px" }}
      >
        직감적으로 골라주세요
      </p>

      {/* 2x2 image grid */}
      <div className="flex-1 flex items-center justify-center mt-lg">
        <AnimatePresence mode="wait">
          <motion.div
            key={round}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="grid grid-cols-2 gap-sm w-full"
            style={{ maxWidth: 400 }}
          >
            {images.map((img) => {
              const isSelected = selected === img.id;
              const isDimmed = selected !== null && !isSelected;

              return (
                <motion.button
                  key={img.id}
                  onClick={() => handleSelect(img.id)}
                  animate={{
                    scale: isSelected ? 0.95 : 1,
                    opacity: isDimmed ? 0.3 : 1,
                  }}
                  transition={{ duration: 0.2 }}
                  className="relative rounded-lg overflow-hidden"
                  style={{
                    aspectRatio: "3 / 4",
                    border: isSelected
                      ? "3px solid #964F4C"
                      : "3px solid transparent",
                  }}
                >
                  {/* Placeholder colored bg until real images are added */}
                  <div
                    className="w-full h-full flex items-center justify-center"
                    style={{
                      backgroundColor: "#F0EDE8",
                    }}
                  >
                    <span
                      className="text-text-tertiary"
                      style={{ fontSize: "13px" }}
                    >
                      {img.alt}
                    </span>
                  </div>
                </motion.button>
              );
            })}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Round indicator dots */}
      <div className="flex justify-center gap-sm mt-lg">
        {Array.from({ length: TOTAL_ROUNDS }).map((_, i) => (
          <div
            key={i}
            className="rounded-full"
            style={{
              width: 8,
              height: 8,
              backgroundColor: i === round ? "#964F4C" : "#E0DCD7",
              transition: "background-color 0.3s",
            }}
          />
        ))}
      </div>
      <p
        className="text-center mt-xs text-text-secondary"
        style={{ fontSize: "13px" }}
      >
        {round + 1} / {TOTAL_ROUNDS}
      </p>

      {/* Bottom links */}
      <div className="flex justify-between items-center mt-lg">
        <button
          onClick={handleSkipAll}
          className="text-text-secondary underline"
          style={{ fontSize: "14px" }}
        >
          건너뛰기
        </button>
        <button
          onClick={handlePass}
          className="text-text-secondary"
          style={{ fontSize: "14px" }}
        >
          패스 →
        </button>
      </div>

      {/* Toast */}
      <AnimatePresence>
        {showToast && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="fixed bottom-24 left-1/2 -translate-x-1/2 px-lg py-sm rounded-full"
            style={{
              backgroundColor: "#964F4C",
              color: "#FFFFFF",
              fontSize: "15px",
              fontWeight: 600,
            }}
          >
            취향 분석 완료!
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
