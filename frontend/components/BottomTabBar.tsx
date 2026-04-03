"use client";

import { usePathname, useRouter } from "next/navigation";
import { motion } from "framer-motion";

const TABS = [
  {
    id: "home",
    label: "홈",
    path: "/feed",
    icon: (active: boolean) => (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={active ? "#964F4C" : "#8C8578"} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
        <polyline points="9 22 9 12 15 12 15 22" />
      </svg>
    ),
  },
  {
    id: "profile",
    label: "마이",
    path: "/profile",
    icon: (active: boolean) => (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={active ? "#964F4C" : "#8C8578"} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
      </svg>
    ),
  },
];

export default function BottomTabBar() {
  const pathname = usePathname();
  const router = useRouter();

  // Don't show on onboarding, outfit detail, or demo page
  if (pathname.startsWith("/onboarding") || pathname.startsWith("/outfit/") || pathname.startsWith("/demo")) {
    return null;
  }

  // iframe 내부에서는 탭바 숨김
  if (typeof window !== "undefined" && window.self !== window.top) {
    return null;
  }

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-50 flex items-end justify-around"
      style={{
        maxWidth: 768,
        margin: "0 auto",
        height: 56,
        backgroundColor: "#F8F6F3",
        borderTop: "1px solid #E5E1DA",
        paddingBottom: "env(safe-area-inset-bottom, 0px)",
      }}
    >
      {TABS.map((tab) => {
        const isActive = pathname === tab.path || pathname.startsWith(tab.path + "/");

        return (
          <button
            key={tab.id}
            onClick={() => router.push(tab.path)}
            className="flex flex-col items-center justify-center flex-1 h-full"
          >
            <motion.div
              key={`${tab.id}-${isActive}`}
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              transition={{
                type: "spring",
                stiffness: 500,
                damping: 20,
              }}
            >
              {tab.icon(isActive)}
            </motion.div>
            <span
              style={{
                fontSize: "11px",
                fontWeight: isActive ? 700 : 400,
                color: isActive ? "#964F4C" : "#B5AFA6",
                marginTop: 2,
              }}
            >
              {tab.label}
            </span>
          </button>
        );
      })}
    </nav>
  );
}
