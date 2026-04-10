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
    if (completed) router.replace("/feed");
  }, [router]);

  if (!mounted) {
    return (
      <main className="flex min-h-dvh flex-col items-center justify-center bg-bg">
        <h1 className="font-display text-4xl font-bold text-accent">ColorFit</h1>
      </main>
    );
  }

  if (isReturning) {
    return (
      <main className="flex min-h-dvh flex-col items-center justify-center bg-bg">
        <h1 className="font-display text-4xl font-bold text-accent">ColorFit</h1>
        <p className="mt-4 text-text-secondary" style={{ fontSize: "14px" }}>코디를 불러오고 있어요...</p>
      </main>
    );
  }

  /* 웰컴 — 스크롤 없이 부모(app-frame) 높이에 맞춤 */
  return (
    <main className="welcome-page">
      {/* BG */}
      <div className="welcome-bg" />
      <div className="welcome-overlay" />

      {/* Content */}
      <div className="welcome-content">
        {/* 브랜드 */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="welcome-brand">
          ColorFit
        </motion.div>

        {/* 중앙 */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="welcome-center">
          <h1 className="welcome-h1">뭘 입을지<br />고민하지 마세요</h1>
          <p className="welcome-desc">퍼스널컬러와 상황에 맞는 코디를 전문가 기준으로 골라드려요</p>

          <div className="welcome-values">
            {["🎨 12톤 퍼스널컬러 매칭", "✓ 상황별 전문가 판단 기준", "🛡 실패 확률 낮은 안전한 선택"].map((t, i) => (
              <motion.div key={i} initial={{ opacity: 0, x: -4 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 + i * 0.06 }} className="welcome-value">
                {t}
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* CTA */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.35 }} className="welcome-cta-wrap">
          <button onClick={() => router.push("/onboarding/step1")} className="welcome-cta">
            1분 만에 내 스타일 찾기
          </button>
          <p className="welcome-sub">간단한 5단계 질문으로 시작해요</p>
        </motion.div>
      </div>
    </main>
  );
}
