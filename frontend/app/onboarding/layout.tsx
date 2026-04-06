"use client";

import { usePathname, useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";

const STEPS = [
  { path: "/onboarding/step1", label: "성별" },
  { path: "/onboarding/step2", label: "퍼스널컬러" },
  { path: "/onboarding/step3", label: "TPO & 무드" },
  { path: "/onboarding/step4", label: "예산" },
  { path: "/onboarding/step5", label: "취향" },
];

function getCurrentStep(pathname: string): number {
  const idx = STEPS.findIndex((s) => pathname.startsWith(s.path));
  return idx >= 0 ? idx : 0;
}

const slideVariants = {
  enter: { x: "60%", opacity: 0 },
  center: { x: 0, opacity: 1 },
  exit: { x: "-30%", opacity: 0 },
};

export default function OnboardingLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const pathname = usePathname();
  const router = useRouter();
  const currentStep = getCurrentStep(pathname);

  const handleBack = () => {
    if (currentStep > 0) router.push(STEPS[currentStep - 1].path);
  };

  return (
    <div className="min-h-dvh bg-bg flex flex-col max-w-[768px] mx-auto">
      {/* Header */}
      <header className="px-[24px] pt-[16px] pb-[8px]">
        <div className="flex items-center justify-between h-[40px]">
          {/* Back */}
          {currentStep > 0 ? (
            <button
              onClick={handleBack}
              className="flex items-center justify-center w-[36px] h-[36px] rounded-full"
              style={{ backgroundColor: "rgba(0,0,0,0.04)" }}
              aria-label="이전"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
                stroke="#222" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M15 18l-6-6 6-6" />
              </svg>
            </button>
          ) : <div style={{ width: 36 }} />}

          {/* Brand */}
          <span className="brand-logo">ColorFit</span>

          {/* Step counter */}
          <span style={{ fontSize: "12px", color: "#B5AFA6", width: 36, textAlign: "right" }}>
            {currentStep + 1}/{STEPS.length}
          </span>
        </div>

        {/* Progress bar */}
        <div className="flex gap-[4px] mt-[12px]">
          {STEPS.map((_, i) => (
            <div
              key={i}
              className="h-[3px] flex-1 rounded-full overflow-hidden"
              style={{ backgroundColor: "#E5E1DA" }}
            >
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: i <= currentStep ? "100%" : "0%" }}
                transition={{ duration: 0.4, ease: "easeOut" }}
                className="h-full rounded-full accent-gradient"
              />
            </div>
          ))}
        </div>
      </header>

      {/* Content */}
      <main className="flex-1 relative overflow-hidden">
        <AnimatePresence mode="wait">
          <motion.div
            key={pathname}
            variants={slideVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{ type: "spring", stiffness: 350, damping: 30 }}
            className="h-full"
          >
            {children}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}
