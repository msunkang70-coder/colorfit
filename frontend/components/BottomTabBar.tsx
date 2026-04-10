"use client";

import { usePathname, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { resetOnboarding } from "@/lib/onboarding-store";

export default function BottomTabBar() {
  const pathname = usePathname();
  const router = useRouter();

  // 온보딩, 첫 화면, 피드에서는 숨김 (피드는 자체 네비게이션 사용)
  if (pathname === "/" || pathname.startsWith("/onboarding") || pathname.startsWith("/outfit/") || pathname === "/feed" || pathname.startsWith("/feed")) {
    return null;
  }

  const isHome = pathname === "/feed" || pathname.startsWith("/feed");

  return (
    <nav
      className="sticky bottom-0 left-0 right-0 z-50"
      style={{
        backgroundColor: "rgba(20,18,16,0.9)",
        backdropFilter: "blur(16px)",
        WebkitBackdropFilter: "blur(16px)",
        borderTop: "1px solid rgba(255,255,255,0.06)",
        flexShrink: 0,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-around", alignItems: "center", height: 56 }}>
        {/* 홈 */}
        <button
          onClick={() => router.push("/feed")}
          className="flex flex-col items-center justify-center flex-1 h-full"
          style={{ gap: 2 }}
        >
          <motion.div animate={{ scale: isHome ? 1.1 : 1 }} transition={{ type: "spring", stiffness: 400, damping: 20 }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill={isHome ? "#964F4C" : "none"} stroke={isHome ? "#964F4C" : "#B5AFA6"} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
              <polyline points="9 22 9 12 15 12 15 22" />
            </svg>
          </motion.div>
          <span style={{ fontSize: "10px", fontWeight: isHome ? 700 : 400, color: isHome ? "#964F4C" : "#B5AFA6" }}>
            홈
          </span>
        </button>

        {/* 다시 진단 */}
        <button
          onClick={() => { resetOnboarding(); router.replace("/onboarding/step1"); }}
          className="flex flex-col items-center justify-center flex-1 h-full"
          style={{ gap: 2 }}
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.35)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="1 4 1 10 7 10" />
            <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
          </svg>
          <span style={{ fontSize: "10px", fontWeight: 400, color: "rgba(255,255,255,0.3)" }}>
            다시 진단
          </span>
        </button>

        {/* 마이 */}
        <button
          onClick={() => router.push("/feed")}
          className="flex flex-col items-center justify-center flex-1 h-full"
          style={{ gap: 2 }}
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.35)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
          <span style={{ fontSize: "10px", fontWeight: 400, color: "rgba(255,255,255,0.3)" }}>
            마이
          </span>
        </button>
      </div>
    </nav>
  );
}
