"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import OutfitCard from "@/components/OutfitCard";
import { getOnboardingData } from "@/lib/onboarding-store";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const TPO_TABS = [
  { id: "", label: "전체" },
  { id: "commute", label: "출근" },
  { id: "interview", label: "면접" },
  { id: "campus", label: "캠퍼스" },
  { id: "date", label: "데이트" },
  { id: "weekend", label: "주말" },
  { id: "travel", label: "여행" },
  { id: "event", label: "행사" },
  { id: "workout", label: "운동" },
];

interface FeedOutfit {
  outfit_id: string;
  items: {
    product_id: string;
    name: string;
    image_url: string;
    price: number;
  }[];
  scores: { pcf: number; of: number } | null;
  reasons: string[];
  total_price: number;
}

interface FeedResponse {
  outfits: FeedOutfit[];
  total_count: number;
  page: number;
  has_next: boolean;
}

type FeedStatus = "idle" | "loading" | "error";

export default function FeedPage() {
  const router = useRouter();
  const profile = getOnboardingData();

  const [activeTpo, setActiveTpo] = useState("");
  const [budgetExpanded, setBudgetExpanded] = useState(false);
  const [budgetMin, setBudgetMin] = useState(profile.budget_min);
  const [budgetMax, setBudgetMax] = useState(profile.budget_max);
  const [outfits, setOutfits] = useState<FeedOutfit[]>([]);
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [status, setStatus] = useState<FeedStatus>("idle");
  const sentinelRef = useRef<HTMLDivElement>(null);
  const loadingRef = useRef(false);

  const fetchFeed = useCallback(
    async (pageNum: number, reset = false) => {
      if (loadingRef.current) return;
      loadingRef.current = true;
      if (reset) setStatus("loading");

      const tpoParam = activeTpo || profile.tpo_list.join(",");
      const params = new URLSearchParams({
        tone_id: profile.tone_id,
        tpo: tpoParam,
        gender: profile.gender,
        budget_min: String(budgetMin),
        budget_max: String(budgetMax),
        page: String(pageNum),
        page_size: "20",
      });

      try {
        const res = await fetch(`${API_BASE}/api/feed?${params}`);
        if (!res.ok) throw new Error(`${res.status}`);
        const data: FeedResponse = await res.json();

        setOutfits((prev) => (reset ? data.outfits : [...prev, ...data.outfits]));
        setHasNext(data.has_next);
        setPage(pageNum);
        setStatus("idle");
      } catch {
        if (reset) setStatus("error");
      } finally {
        loadingRef.current = false;
      }
    },
    [activeTpo, budgetMin, budgetMax, profile],
  );

  // Initial load + filter change
  useEffect(() => {
    fetchFeed(1, true);
  }, [fetchFeed]);

  // Infinite scroll via IntersectionObserver
  useEffect(() => {
    const el = sentinelRef.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasNext && !loadingRef.current) {
          fetchFeed(page + 1);
        }
      },
      { rootMargin: "200px" },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [hasNext, page, fetchFeed]);

  const handleTpoChange = (tpo: string) => {
    setActiveTpo(tpo);
  };

  const handleCardTap = (outfitId: string) => {
    router.push(`/outfit/${outfitId}`);
  };

  // Today's top pick (first outfit)
  const topPick = outfits[0];
  const regularOutfits = outfits.slice(1);

  return (
    <div className="min-h-dvh bg-bg max-w-[768px] mx-auto">
      {/* Header */}
      <header className="sticky top-0 z-30 bg-bg px-md pt-md pb-sm">
        <div className="flex items-center justify-between">
          <h1
            style={{
              fontFamily: "var(--font-display)",
              fontSize: "20px",
              fontWeight: 700,
            }}
          >
            ColorFit
          </h1>
          <button
            className="w-8 h-8 rounded-full bg-surface flex items-center justify-center"
            aria-label="프로필"
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
            >
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          </button>
        </div>

        {/* TPO tabs */}
        <div className="flex gap-sm mt-sm overflow-x-auto scrollbar-hide pb-xs">
          {TPO_TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => handleTpoChange(tab.id)}
              className="shrink-0 px-md py-xs rounded-full whitespace-nowrap"
              style={{
                fontSize: "13px",
                fontWeight: 500,
                backgroundColor: activeTpo === tab.id ? "#964F4C" : "#FFFFFF",
                color: activeTpo === tab.id ? "#FFFFFF" : "#222222",
                border:
                  activeTpo === tab.id
                    ? "1.5px solid #964F4C"
                    : "1.5px solid #E0DCD7",
                transition: "background-color 0.2s, color 0.2s",
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Budget slider (collapsible) */}
        <button
          onClick={() => setBudgetExpanded((v) => !v)}
          className="mt-xs text-text-secondary"
          style={{ fontSize: "13px" }}
        >
          ₩{budgetMin.toLocaleString()}~₩{budgetMax.toLocaleString()}{" "}
          <span style={{ fontSize: "11px" }}>{budgetExpanded ? "▲" : "▼"}</span>
        </button>

        <AnimatePresence>
          {budgetExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: "easeOut" as const }}
              className="overflow-hidden"
            >
              <div className="flex gap-sm items-center mt-sm pb-sm">
                <input
                  type="range"
                  min={0}
                  max={300000}
                  step={10000}
                  value={budgetMin}
                  onChange={(e) =>
                    setBudgetMin(Math.min(+e.target.value, budgetMax - 10000))
                  }
                  className="flex-1 accent-accent"
                />
                <input
                  type="range"
                  min={0}
                  max={300000}
                  step={10000}
                  value={budgetMax}
                  onChange={(e) =>
                    setBudgetMax(Math.max(+e.target.value, budgetMin + 10000))
                  }
                  className="flex-1 accent-accent"
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </header>

      {/* Content */}
      <main>
        {/* Loading skeleton */}
        {status === "loading" && (
          <div className="px-[20px]">
            {[0, 1, 2].map((i) => (
              <div key={i} className="mb-[20px] animate-pulse">
                <div
                  className="w-full rounded-lg"
                  style={{
                    aspectRatio: "3 / 4",
                    backgroundColor: "#E0DCD7",
                  }}
                />
                <div className="mt-3 h-4 w-2/3 rounded bg-[#E0DCD7]" />
                <div className="mt-2 h-3 w-1/3 rounded bg-[#E0DCD7]" />
              </div>
            ))}
          </div>
        )}

        {/* Error state */}
        {status === "error" && (
          <div className="flex flex-col items-center justify-center py-3xl">
            <p style={{ fontSize: "16px" }}>불러오지 못했어요</p>
            <button
              onClick={() => fetchFeed(1, true)}
              className="mt-md px-lg py-sm rounded-lg"
              style={{
                fontSize: "14px",
                border: "1.5px solid #964F4C",
                color: "#964F4C",
              }}
            >
              다시 시도
            </button>
          </div>
        )}

        {/* Empty state */}
        {status === "idle" && outfits.length === 0 && (
          <div className="flex flex-col items-center justify-center py-3xl">
            <p
              className="text-text-secondary"
              style={{ fontSize: "40px", lineHeight: 1 }}
            >
              👗
            </p>
            <p className="mt-md" style={{ fontSize: "16px" }}>
              조건에 맞는 코디가 없어요
            </p>
            <button
              onClick={() => {
                setActiveTpo("");
                setBudgetMin(0);
                setBudgetMax(300000);
              }}
              className="mt-md px-lg py-sm rounded-lg text-white"
              style={{ fontSize: "14px", backgroundColor: "#964F4C" }}
            >
              필터를 변경해보세요
            </button>
          </div>
        )}

        {/* Today's ColorFit (top pick) */}
        {status === "idle" && topPick && (
          <section
            className="mx-[20px] mb-[20px] rounded-2xl"
            style={{ backgroundColor: "#F0EDE8", padding: 24 }}
          >
            <p
              style={{
                fontFamily: "var(--font-display)",
                fontSize: "18px",
                color: "#964F4C",
                fontWeight: 700,
                marginBottom: 16,
              }}
            >
              오늘의 컬러핏
            </p>
            <OutfitCard
              outfitId={topPick.outfit_id}
              imageUrl={topPick.items[0]?.image_url ?? ""}
              title={topPick.reasons[0] ?? "추천 코디"}
              totalPrice={topPick.total_price}
              itemCount={topPick.items.length}
              reason={topPick.reasons[1] ?? ""}
              scores={{
                pcf: topPick.scores?.pcf ?? 0,
                of: topPick.scores?.of ?? 0,
              }}
              onTap={handleCardTap}
              index={0}
            />
          </section>
        )}

        {/* Regular outfit cards */}
        {status === "idle" &&
          regularOutfits.map((outfit, i) => (
            <OutfitCard
              key={outfit.outfit_id}
              outfitId={outfit.outfit_id}
              imageUrl={outfit.items[0]?.image_url ?? ""}
              title={outfit.reasons[0] ?? "추천 코디"}
              totalPrice={outfit.total_price}
              itemCount={outfit.items.length}
              reason={outfit.reasons[1] ?? ""}
              scores={{
                pcf: outfit.scores?.pcf ?? 0,
                of: outfit.scores?.of ?? 0,
              }}
              onTap={handleCardTap}
              index={i + 1}
            />
          ))}

        {/* Infinite scroll sentinel */}
        <div ref={sentinelRef} style={{ height: 1 }} />

        {/* Bottom padding for tab bar */}
        <div style={{ height: 80 }} />
      </main>
    </div>
  );
}
