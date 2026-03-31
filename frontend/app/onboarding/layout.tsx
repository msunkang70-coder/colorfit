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
  enter: (direction: number) => ({
    x: direction > 0 ? "100%" : "-100%",
    opacity: 0,
  }),
  center: {
    x: 0,
    opacity: 1,
  },
  exit: (direction: number) => ({
    x: direction > 0 ? "-100%" : "100%",
    opacity: 0,
  }),
};

const slideTransition = {
  type: "spring" as const,
  stiffness: 300,
  damping: 30,
};

export default function OnboardingLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const pathname = usePathname();
  const router = useRouter();
  const currentStep = getCurrentStep(pathname);

  const handleBack = () => {
    if (currentStep > 0) {
      router.push(STEPS[currentStep - 1].path);
    }
  };

  return (
    <div className="min-h-dvh bg-bg flex flex-col max-w-[768px] mx-auto">
      {/* Header: Back button + Progress bar */}
      <header className="px-md pt-md pb-sm">
        {/* Back button */}
        <div className="h-10 flex items-center">
          {currentStep > 0 && (
            <button
              onClick={handleBack}
              className="flex items-center justify-center w-10 h-10 -ml-2 rounded-full"
              aria-label="이전 단계"
            >
              <svg
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M15 18l-6-6 6-6" />
              </svg>
            </button>
          )}
        </div>

        {/* Progress bar */}
        <div className="flex gap-[6px] mt-sm">
          {STEPS.map((_, i) => (
            <div
              key={i}
              className="h-[3px] flex-1 rounded-full transition-colors duration-300"
              style={{
                backgroundColor: i <= currentStep ? "#964F4C" : "#E0DCD7",
              }}
            />
          ))}
        </div>

        {/* Step label */}
        <p
          className="mt-xs text-center"
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "13px",
            color: "#8C8578",
          }}
        >
          {currentStep + 1} / {STEPS.length} · {STEPS[currentStep].label}
        </p>
      </header>

      {/* Content with slide transition */}
      <main className="flex-1 relative overflow-hidden">
        <AnimatePresence mode="wait" custom={1}>
          <motion.div
            key={pathname}
            custom={1}
            variants={slideVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={slideTransition}
            className="h-full"
          >
            {children}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}
