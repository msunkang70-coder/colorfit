"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { updateOnboarding, getOnboardingData } from "@/lib/onboarding-store";
import { postOnboarding } from "@/lib/api";

interface StyleImage {
  id: string;
  src: string;
  label: string;
  sub?: string;
}

const ROUND_TITLES = [
  { title: "어떤 무드가 좋아요?", sub: "끌리는 스타일을 골라주세요" },
  { title: "어떤 장르를 선호해요?", sub: "평소 좋아하는 느낌을 골라주세요" },
  { title: "어떤 핏이 편해요?", sub: "자주 입는 실루엣을 골라주세요" },
  { title: "어떤 컬러가 좋아요?", sub: "끌리는 색감을 골라주세요" },
];

// ── 여성 라운드 정의 ──
const FEMALE_ROUNDS: StyleImage[][] = [
  // 라운드1: 무드 (스타일 축)
  [
    { id: "r1-1", src: "/images/style/style_1.jpg", label: "미니멀", sub: "군더더기 없이 깔끔한" },
    { id: "r1-2", src: "/images/style/style_2.jpg", label: "캐주얼", sub: "편안하고 자연스러운" },
    { id: "r1-3", src: "/images/style/style_3.jpg", label: "스트릿", sub: "개성과 트렌드가 살아있는" },
    { id: "r1-4", src: "/images/style/style_4.jpg", label: "페미닌", sub: "여성스럽고 우아한" },
  ],
  // 라운드2: 장르 (스타일 축)
  [
    { id: "r2-1", src: "/images/style/style_5.jpg", label: "모던 오피스", sub: "깔끔한 비즈니스룩" },
    { id: "r2-2", src: "/images/style/style_6.jpg", label: "빈티지", sub: "클래식한 복고 감성" },
    { id: "r2-3", src: "/images/style/style_7.jpg", label: "스포티", sub: "활동적이고 건강한" },
    { id: "r2-4", src: "/images/style/style_8.jpg", label: "클래식", sub: "시간이 지나도 멋스러운" },
  ],
  // 라운드3: 핏 (실루엣 축 — 순수 핏만)
  [
    { id: "r3-1", src: "/images/style/female_fit_oversize.jpg", label: "오버사이즈", sub: "여유 있는 편안한 실루엣" },
    { id: "r3-2", src: "/images/style/female_fit_regular.jpg", label: "레귤러핏", sub: "기본에 충실한 표준 핏" },
    { id: "r3-3", src: "/images/style/female_fit_slim.jpg", label: "슬림핏", sub: "몸에 맞는 깔끔한 라인" },
  ],
  // 라운드4: 컬러 (채도 축 — 단일 기준)
  [
    { id: "r4-1", src: "/images/style/female_color_mono.jpg", label: "모노톤", sub: "블랙·화이트·그레이" },
    { id: "r4-2", src: "/images/style/female_color_neutral.jpg", label: "뉴트럴", sub: "베이지·아이보리 중심" },
    { id: "r4-3", src: "/images/style/female_color_pastel.jpg", label: "파스텔", sub: "부드럽고 연한 색감" },
    { id: "r4-4", src: "/images/style/female_color_vivid.jpg", label: "비비드", sub: "선명하고 포인트 되는 컬러" },
  ],
];

// ── 남성 라운드 정의 ──
const MALE_ROUNDS: StyleImage[][] = [
  // 라운드1: 무드 (스타일 축)
  [
    { id: "r1-1", src: "/images/style/male_1.jpg", label: "미니멀", sub: "군더더기 없이 깔끔한" },
    { id: "r1-2", src: "/images/style/male_2.jpg", label: "캐주얼", sub: "편안하고 자연스러운" },
    { id: "r1-3", src: "/images/style/male_3.jpg", label: "스트릿", sub: "개성과 트렌드가 살아있는" },
    { id: "r1-4", src: "/images/style/male_4.jpg", label: "댄디", sub: "단정하고 세련된" },
  ],
  // 라운드2: 장르 (스타일 축)
  [
    { id: "r2-1", src: "/images/style/male_5.jpg", label: "모던 오피스", sub: "깔끔한 비즈니스룩" },
    { id: "r2-2", src: "/images/style/male_6.jpg", label: "아메카지", sub: "빈티지 워크웨어 감성" },
    { id: "r2-3", src: "/images/style/male_7.jpg", label: "스포티", sub: "활동적이고 건강한" },
    { id: "r2-4", src: "/images/style/male_8.jpg", label: "클래식", sub: "시간이 지나도 멋스러운" },
  ],
  // 라운드3: 핏 (실루엣 축 — 순수 핏만)
  [
    { id: "r3-1", src: "/images/style/male_fit_oversize.jpg", label: "오버사이즈", sub: "여유 있는 편안한 실루엣" },
    { id: "r3-2", src: "/images/style/male_fit_regular.jpg", label: "레귤러핏", sub: "기본에 충실한 표준 핏" },
    { id: "r3-3", src: "/images/style/male_fit_slim.jpg", label: "슬림핏", sub: "몸에 맞는 깔끔한 라인" },
  ],
  // 라운드4: 컬러 (채도 축 — 단일 기준)
  [
    { id: "r4-1", src: "/images/style/male_color_mono.jpg", label: "모노톤", sub: "블랙·화이트·그레이" },
    { id: "r4-2", src: "/images/style/male_color_neutral.jpg", label: "뉴트럴", sub: "베이지·아이보리 중심" },
    { id: "r4-3", src: "/images/style/male_color_pastel.jpg", label: "파스텔", sub: "부드럽고 연한 색감" },
    { id: "r4-4", src: "/images/style/male_color_vivid.jpg", label: "비비드", sub: "선명하고 포인트 되는 컬러" },
  ],
];

const TOTAL_ROUNDS = 4;

export default function Step5Page() {
  const router = useRouter();
  const [round, setRound] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);
  const [showToast, setShowToast] = useState(false);
  const [gender, setGender] = useState("female");
  const choices = useRef<{ round: number; image_id: string }[]>([]);

  useEffect(() => {
    const data = getOnboardingData();
    if (data.gender) setGender(data.gender);
  }, []);

  const rounds = gender === "male" ? MALE_ROUNDS : FEMALE_ROUNDS;
  const isLastRound = round === TOTAL_ROUNDS - 1;
  const images = rounds[round];
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

      {/* Image Grid — 3장이면 2+1, 4장이면 2x2 */}
      <div className="flex-1 flex items-center justify-center mt-[20px]">
        <AnimatePresence mode="wait">
          <motion.div
            key={round}
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.97 }}
            transition={{ duration: 0.25 }}
            className={`grid gap-[10px] w-full ${images.length === 3 ? "grid-cols-2" : "grid-cols-2"}`}
            style={{ maxWidth: 360 }}
          >
            {images.map((img, imgIdx) => {
              const isSelected = selected === img.id;
              const isDimmed = selected !== null && !isSelected;
              const isLastOdd = images.length % 2 === 1 && imgIdx === images.length - 1;

              return (
                <motion.button
                  key={img.id}
                  onClick={() => handleSelect(img.id)}
                  animate={{
                    scale: isSelected ? 0.96 : 1,
                    opacity: isDimmed ? 0.3 : 1,
                  }}
                  transition={{ duration: 0.25 }}
                  className={`relative rounded-xl overflow-hidden ${isLastOdd ? "col-span-2 mx-auto" : ""}`}
                  style={{
                    ...(isLastOdd ? { maxWidth: "calc(50% - 5px)" } : {}),
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
                    style={{ background: "linear-gradient(transparent, rgba(0,0,0,0.55))" }}
                  >
                    <span
                      style={{
                        fontSize: "13px",
                        fontWeight: 600,
                        color: "#FFFFFF",
                        letterSpacing: "0.3px",
                        display: "block",
                      }}
                    >
                      {img.label}
                    </span>
                    {img.sub && (
                      <span
                        style={{
                          fontSize: "10px",
                          fontWeight: 400,
                          color: "rgba(255,255,255,0.8)",
                          display: "block",
                          marginTop: 2,
                        }}
                      >
                        {img.sub}
                      </span>
                    )}
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
