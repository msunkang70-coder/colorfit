"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { getOnboardingData } from "@/lib/onboarding-store";

export default function Home() {
  const router = useRouter();
  const [isReturning, setIsReturning] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const data = getOnboardingData();
    const completed = Boolean(data.tone_id && data.tpo_list.length > 0);
    setIsReturning(completed);
    setMounted(true);

    // 기존 사용자는 자동으로 피드 이동
    if (completed) {
      router.replace("/feed");
    }
  }, [router]);

  if (!mounted) {
    return (
      <main className="flex min-h-dvh flex-col items-center justify-center bg-bg">
        <h1 className="font-display text-4xl font-bold text-accent">ColorFit</h1>
      </main>
    );
  }

  // 기존 사용자 → 피드로 리다이렉트 중
  if (isReturning) {
    return (
      <main className="flex min-h-dvh flex-col items-center justify-center bg-bg">
        <h1 className="font-display text-4xl font-bold text-accent">ColorFit</h1>
        <p className="mt-4 text-text-secondary" style={{ fontSize: "14px" }}>
          코디를 불러오고 있어요...
        </p>
      </main>
    );
  }

  // 신규 사용자 → 웰컴 화면
  return (
    <main className="flex min-h-dvh flex-col items-center justify-center bg-bg px-[24px]">
      <motion.div
        className="flex flex-col items-center text-center max-w-[360px]"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1 className="font-display text-[40px] font-bold text-accent leading-tight">
          ColorFit
        </h1>
        <p className="mt-[12px] text-text-secondary" style={{ fontSize: "15px", lineHeight: 1.6 }}>
          퍼스널컬러에 맞는 코디를 추천하고<br />
          왜 이 코디인지 설명해드려요
        </p>

        <motion.button
          onClick={() => router.push("/onboarding/step1")}
          className="w-full mt-[40px] cta-primary"
          whileTap={{ scale: 0.97 }}
        >
          내 스타일 진단 시작하기
        </motion.button>

        <p className="mt-[16px] text-text-tertiary" style={{ fontSize: "12px" }}>
          1분이면 끝나요 — 성별, 퍼스널컬러, 상황, 예산, 취향
        </p>
      </motion.div>
    </main>
  );
}
