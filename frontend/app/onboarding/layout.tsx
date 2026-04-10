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

export default function OnboardingLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const pathname = usePathname();
  const router = useRouter();
  const currentStep = getCurrentStep(pathname);

  const handleBack = () => {
    if (currentStep > 0) router.push(STEPS[currentStep - 1].path);
    else router.push("/");
  };

  return (
    <div className="onboarding-shell">
      {/* Header — 컴팩트 */}
      <header className="onboarding-header">
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", height: 36 }}>
          <button
            onClick={handleBack}
            className="flex items-center justify-center"
            style={{ width: 32, height: 32, borderRadius: 16, backgroundColor: "rgba(255,255,255,0.1)" }}
            aria-label="이전"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
              stroke="rgba(255,255,255,0.7)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M15 18l-6-6 6-6" />
            </svg>
          </button>

          <span style={{ fontFamily: "var(--font-display)", fontSize: "15px", fontWeight: 700, color: "#964F4C", letterSpacing: "1px" }}>
            ColorFit
          </span>

          <span style={{ fontSize: "11px", color: "rgba(255,255,255,0.4)", width: 32, textAlign: "right" }}>
            {currentStep + 1}/{STEPS.length}
          </span>
        </div>

        {/* Progress bar */}
        <div style={{ display: "flex", gap: 3, marginTop: 8 }}>
          {STEPS.map((_, i) => (
            <div
              key={i}
              style={{
                flex: 1,
                height: 3,
                borderRadius: 2,
                overflow: "hidden",
                backgroundColor: "rgba(255,255,255,0.12)",
              }}
            >
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: i <= currentStep ? "100%" : "0%" }}
                transition={{ duration: 0.4, ease: "easeOut" }}
                style={{ height: "100%", borderRadius: 2, background: "linear-gradient(90deg, #964F4C, #B5605D)" }}
              />
            </div>
          ))}
        </div>
      </header>

      {/* Content */}
      <main className="onboarding-main">
        <AnimatePresence mode="wait">
          <motion.div
            key={pathname}
            initial={{ x: "40%", opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: "-20%", opacity: 0 }}
            transition={{ type: "spring", stiffness: 350, damping: 30 }}
            style={{ height: "100%" }}
          >
            {children}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}
