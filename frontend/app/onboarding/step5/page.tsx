"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { updateOnboarding, getOnboardingData } from "@/lib/onboarding-store";
import { postOnboarding } from "@/lib/api";

interface StyleImage {
  id: string;
  src: string;
  label: string;
}

const ROUND_TITLES = [
  { title: "어떤 무드가 좋아요?", sub: "끌리는 스타일을 골라주세요" },
  { title: "어떤 장르를 선호해요?", sub: "평소 좋아하는 느낌을 골라주세요" },
  { title: "어떤 핏이 편해요?", sub: "자주 입는 실루엣을 골라주세요" },
  { title: "어떤 컬러가 좋아요?", sub: "끌리는 색감을 골라주세요" },
];

const ROUNDS: StyleImage[][] = [
  [
    { id: "r1-1", src: "/images/style/style_1.jpg", label: "미니멀" },
    { id: "r1-2", src: "/images/style/style_2.jpg", label: "캐주얼" },
    { id: "r1-3", src: "/images/style/style_3.jpg", label: "스트릿" },
    { id: "r1-4", src: "/images/style/style_4.jpg", label: "페미닌" },
  ],
  [
    { id: "r2-1", src: "/images/style/style_5.jpg", label: "모던 오피스" },
    { id: "r2-2", src: "/images/style/style_6.jpg", label: "빈티지" },
    { id: "r2-3", src: "/images/style/style_7.jpg", label: "스포티" },
    { id: "r2-4", src: "/images/style/style_8.jpg", label: "클래식" },
  ],
  [
    { id: "r3-1", src: "/images/style/style_9.jpg", label: "오버사이즈" },
    { id: "r3-2", src: "/images/style/style_10.jpg", label: "슬림핏" },
    { id: "r3-3", src: "/images/style/style_11.jpg", label: "A라인" },
    { id: "r3-4", src: "/images/style/style_12.jpg", label: "레이어드" },
  ],
  [
    { id: "r4-1", src: "/images/style/style_13.jpg", label: "뉴트럴" },
    { id: "r4-2", src: "/images/style/style_14.jpg", label: "비비드" },
    { id: "r4-3", src: "/images/style/style_15.jpg", label: "파스텔" },
    { id: "r4-4", src: "/images/style/style_16.jpg", label: "모노톤" },
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
  const roundInfo = ROUND_TITLES[round];

  const submitOnboarding = async () => {
    updateOnboarding({ style_seed_choices: choices.current });
    const data = getOnboardingData();
    try { await postOnboarding(data); } catch {}
  };

  const goToFeed = async () => {
    setShowToast(true);
    await submitOnboarding();
    setTimeout(() => router.push("/feed"), 1200);
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
    setTimeout(advanceRound, 600);
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
    <div className="flex flex-col min-h-full px-[20px] pb-[24px]">
      {/* Headline */}
      <div className="mt-[8px]">
        <motion.h2
          key={`title-${round}`}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          style={{
            fontFamily: "var(--font-display)",
            fontSize: "22px",
            fontWeight: 700,
            color: "#222",
            lineHeight: 1.3,
          }}
        >
          {roundInfo.title}
        </motion.h2>
        <motion.p
          key={`sub-${round}`}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1, duration: 0.3 }}
          style={{ fontSize: "13px", color: "#8C8578", marginTop: 6 }}
        >
          {roundInfo.sub}
        </motion.p>
      </div>

      {/* 2x2 Image Grid */}
      <div className="flex-1 flex items-center justify-center mt-[20px]">
        <AnimatePresence mode="wait">
          <motion.div
            key={round}
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.97 }}
            transition={{ duration: 0.25 }}
            className="grid grid-cols-2 gap-[10px] w-full"
            style={{ maxWidth: 360 }}
          >
            {images.map((img) => {
              const isSelected = selected === img.id;
              const isDimmed = selected !== null && !isSelected;

              return (
                <motion.button
                  key={img.id}
                  onClick={() => handleSelect(img.id)}
                  animate={{
                    scale: isSelected ? 0.96 : 1,
                    opacity: isDimmed ? 0.3 : 1,
                  }}
                  transition={{ duration: 0.25 }}
                  className="relative rounded-xl overflow-hidden"
                  style={{
                    aspectRatio: "3 / 4",
                    border: isSelected ? "3px solid #964F4C" : "2px solid transparent",
                    boxShadow: isSelected ? "0 4px 20px rgba(150,79,76,0.2)" : "0 2px 8px rgba(0,0,0,0.06)",
                  }}
                >
                  {/* Image */}
                  <img
                    src={img.src}
                    alt={img.label}
                    loading="lazy"
                    className="w-full h-full object-cover"
                    referrerPolicy="no-referrer"
                  />

                  {/* Label overlay */}
                  <div
                    className="absolute bottom-0 left-0 right-0 px-[10px] pb-[10px] pt-[28px]"
                    style={{ background: "linear-gradient(transparent, rgba(0,0,0,0.45))" }}
                  >
                    <span
                      style={{
                        fontSize: "13px",
                        fontWeight: 600,
                        color: "#FFFFFF",
                        letterSpacing: "0.3px",
                      }}
                    >
                      {img.label}
                    </span>
                  </div>

                  {/* Selected check */}
                  {isSelected && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="absolute top-[8px] right-[8px] w-[28px] h-[28px] rounded-full flex items-center justify-center"
                      style={{ backgroundColor: "#964F4C" }}
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    </motion.div>
                  )}
                </motion.button>
              );
            })}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Round indicator */}
      <div className="flex justify-center gap-[6px] mt-[20px]">
        {Array.from({ length: TOTAL_ROUNDS }).map((_, i) => (
          <div
            key={i}
            className="rounded-full"
            style={{
              width: i === round ? 20 : 6,
              height: 6,
              borderRadius: 3,
              backgroundColor: i === round ? "#964F4C" : "#E5E1DA",
              transition: "all 0.3s ease",
            }}
          />
        ))}
      </div>

      {/* Bottom */}
      <div className="flex justify-between items-center mt-[16px]">
        <button
          onClick={handleSkipAll}
          style={{ fontSize: "12px", color: "#B5AFA6", background: "none", border: "none", cursor: "pointer" }}
        >
          건너뛰기
        </button>
        <button
          onClick={handlePass}
          style={{ fontSize: "13px", color: "#8C8578", background: "none", border: "none", cursor: "pointer", fontWeight: 500 }}
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
            className="fixed bottom-24 left-1/2 -translate-x-1/2 px-[24px] py-[12px] rounded-full"
            style={{
              background: "linear-gradient(135deg, #964F4C, #B5605D)",
              color: "#FFFFFF",
              fontSize: "14px",
              fontWeight: 600,
              boxShadow: "0 4px 16px rgba(150,79,76,0.3)",
            }}
          >
            ✨ 취향 분석 완료!
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
