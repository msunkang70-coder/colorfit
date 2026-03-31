"use client";

import { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion, useScroll, useTransform } from "framer-motion";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface ItemData {
  product_id: string;
  category: string;
  name: string;
  brand: string;
  price: number;
  image_url: string;
  mall_url: string;
}

interface ScoresData {
  pcf: number;
  of: number;
  ch: number;
  pe: number;
  sf: number;
  total: number;
}

interface OutfitData {
  outfit_id: string;
  items: ItemData[];
  scores: ScoresData | null;
  reasons: string[];
  total_price: number;
}

const SCORE_AXES = [
  { key: "pcf" as const, label: "퍼스널컬러", color: "#964F4C" },
  { key: "of" as const, label: "TPO 적합", color: "#4F97A3" },
  { key: "ch" as const, label: "색상 조화", color: "#DDB67D" },
  { key: "pe" as const, label: "가격 효율", color: "#D1933F" },
  { key: "sf" as const, label: "스타일 핏", color: "#6B5876" },
];

type PageStatus = "loading" | "error" | "success";

function formatPrice(price: number): string {
  return `₩${price.toLocaleString("ko-KR")}`;
}

export default function OutfitDetailPage() {
  const params = useParams();
  const router = useRouter();
  const outfitId = params.id as string;

  const [outfit, setOutfit] = useState<OutfitData | null>(null);
  const [status, setStatus] = useState<PageStatus>("loading");
  const [saved, setSaved] = useState(false);
  const heroRef = useRef<HTMLDivElement>(null);

  const { scrollY } = useScroll();
  const heroScale = useTransform(scrollY, [0, 300], [1, 0.85]);
  const heroOpacity = useTransform(scrollY, [0, 200], [1, 0.6]);

  useEffect(() => {
    async function fetchOutfit() {
      setStatus("loading");
      try {
        const res = await fetch(`${API_BASE}/api/outfit/${outfitId}`);
        if (!res.ok) throw new Error(`${res.status}`);
        const data: OutfitData = await res.json();
        setOutfit(data);
        setStatus("success");
      } catch {
        setStatus("error");
      }
    }
    fetchOutfit();
  }, [outfitId]);

  const lowestPrice = outfit
    ? outfit.items.reduce((sum, it) => sum + it.price, 0)
    : 0;

  return (
    <div className="min-h-dvh bg-bg max-w-[768px] mx-auto">
      {/* Loading */}
      {status === "loading" && (
        <div>
          <div
            className="w-full animate-pulse"
            style={{ aspectRatio: "3 / 4", backgroundColor: "#E0DCD7" }}
          />
          <div className="p-[20px]">
            <div className="h-5 w-2/3 rounded bg-[#E0DCD7] mb-3" />
            <div className="h-4 w-1/3 rounded bg-[#E0DCD7] mb-3" />
            <div className="h-3 w-full rounded bg-[#E0DCD7] mb-2" />
            <div className="h-3 w-full rounded bg-[#E0DCD7]" />
          </div>
        </div>
      )}

      {/* Error */}
      {status === "error" && (
        <div className="flex flex-col items-center justify-center min-h-dvh">
          <p style={{ fontSize: "16px" }}>코디 정보를 불러오지 못했어요</p>
          <button
            onClick={() => router.back()}
            className="mt-md px-lg py-sm rounded-lg"
            style={{
              fontSize: "14px",
              border: "1.5px solid #964F4C",
              color: "#964F4C",
            }}
          >
            뒤로가기
          </button>
        </div>
      )}

      {/* Success */}
      {status === "success" && outfit && (
        <>
          {/* Hero image */}
          <motion.div
            ref={heroRef}
            style={{ scale: heroScale, opacity: heroOpacity }}
            className="relative w-full overflow-hidden"
          >
            <div
              className="w-full"
              style={{ aspectRatio: "3 / 4" }}
            >
              {outfit.items[0]?.image_url ? (
                <img
                  src={outfit.items[0].image_url}
                  alt="코디 이미지"
                  width={768}
                  height={1024}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full bg-surface flex items-center justify-center">
                  <span className="text-text-tertiary">이미지 없음</span>
                </div>
              )}
            </div>

            {/* Back button */}
            <button
              onClick={() => router.back()}
              className="absolute top-4 left-4 w-10 h-10 rounded-full flex items-center justify-center"
              style={{ backgroundColor: "rgba(255,255,255,0.7)" }}
            >
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#222222"
                strokeWidth="1.5"
              >
                <path d="M15 18l-6-6 6-6" />
              </svg>
            </button>

            {/* Save button */}
            <button
              onClick={() => setSaved((v) => !v)}
              className="absolute top-4 right-4 w-10 h-10 rounded-full flex items-center justify-center"
              style={{ backgroundColor: "rgba(255,255,255,0.7)" }}
            >
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill={saved ? "#964F4C" : "none"}
                stroke={saved ? "#964F4C" : "#222222"}
                strokeWidth="1.5"
              >
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
              </svg>
            </button>
          </motion.div>

          {/* Content */}
          <div className="relative bg-bg -mt-4 rounded-t-xl" style={{ padding: "20px" }}>
            {/* Title + Price */}
            <h2
              style={{
                fontFamily: "var(--font-display)",
                fontSize: "22px",
                fontWeight: 700,
                color: "#222222",
              }}
            >
              {outfit.reasons[0] ?? "추천 코디"}
            </h2>
            <p
              className="mt-[4px] font-bold"
              style={{ fontSize: "20px", color: "#222222" }}
            >
              {formatPrice(outfit.total_price)}
            </p>

            {/* Score bars */}
            {outfit.scores && (
              <section className="mt-xl">
                <h3
                  className="mb-md"
                  style={{
                    fontFamily: "var(--font-display)",
                    fontSize: "16px",
                    fontWeight: 700,
                  }}
                >
                  스코어 분석
                </h3>
                <div className="flex flex-col gap-[12px]">
                  {SCORE_AXES.map((axis, i) => {
                    const value = outfit.scores![axis.key];
                    return (
                      <div key={axis.key} className="flex items-center gap-sm">
                        <span
                          className="shrink-0"
                          style={{
                            width: 72,
                            fontSize: "13px",
                            color: "#8C8578",
                          }}
                        >
                          {axis.label}
                        </span>
                        <div
                          className="flex-1 rounded-full overflow-hidden"
                          style={{ height: 8, backgroundColor: "#E0DCD7" }}
                        >
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${value}%` }}
                            transition={{
                              duration: 0.8,
                              delay: i * 0.15,
                              ease: "easeOut" as const,
                            }}
                            className="h-full rounded-full"
                            style={{ backgroundColor: axis.color }}
                          />
                        </div>
                        <span
                          className="shrink-0"
                          style={{
                            width: 28,
                            fontSize: "13px",
                            fontWeight: 600,
                            textAlign: "right",
                            color: axis.color,
                          }}
                        >
                          {Math.round(value)}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </section>
            )}

            {/* Reasons card */}
            {outfit.reasons.length > 0 && (
              <section
                className="mt-xl rounded-xl"
                style={{
                  backgroundColor: "#F0EDE8",
                  padding: 16,
                }}
              >
                <h3
                  className="mb-sm"
                  style={{
                    fontFamily: "var(--font-display)",
                    fontSize: "15px",
                    fontWeight: 700,
                  }}
                >
                  추천 이유
                </h3>
                <ul className="flex flex-col gap-[6px]">
                  {outfit.reasons.map((r, i) => (
                    <li
                      key={i}
                      className="text-text-secondary"
                      style={{ fontSize: "13px", lineHeight: 1.5 }}
                    >
                      • {r}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {/* Items carousel */}
            <section className="mt-xl">
              <h3
                className="mb-md"
                style={{
                  fontFamily: "var(--font-display)",
                  fontSize: "16px",
                  fontWeight: 700,
                }}
              >
                아이템 구성
              </h3>
              <div className="flex gap-md overflow-x-auto scrollbar-hide pb-sm">
                {outfit.items.map((item) => (
                  <div
                    key={item.product_id}
                    className="shrink-0 flex flex-col"
                    style={{ width: 100 }}
                  >
                    <div
                      className="rounded-md overflow-hidden bg-surface"
                      style={{ width: 80, height: 80 }}
                    >
                      {item.image_url ? (
                        <img
                          src={item.image_url}
                          alt={item.name}
                          loading="lazy"
                          width={80}
                          height={80}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <span
                            className="text-text-tertiary"
                            style={{ fontSize: "10px" }}
                          >
                            {item.category}
                          </span>
                        </div>
                      )}
                    </div>
                    <span
                      className="mt-[4px] text-text-secondary truncate"
                      style={{ fontSize: "11px" }}
                    >
                      {item.brand}
                    </span>
                    <span
                      className="truncate"
                      style={{ fontSize: "13px" }}
                    >
                      {item.name}
                    </span>
                    <span
                      className="font-bold"
                      style={{ fontSize: "14px" }}
                    >
                      {formatPrice(item.price)}
                    </span>
                  </div>
                ))}
              </div>
            </section>

            {/* Price summary */}
            <div
              className="mt-xl pt-md"
              style={{ borderTop: "1px solid #E5E1DA" }}
            >
              <div className="flex justify-between">
                <span style={{ fontSize: "15px" }}>코디 합계</span>
                <span className="font-bold" style={{ fontSize: "15px" }}>
                  {formatPrice(outfit.total_price)}
                </span>
              </div>
              <div className="flex justify-between mt-xs">
                <span style={{ fontSize: "15px" }}>최저가 합산</span>
                <span
                  className="font-bold"
                  style={{ fontSize: "15px", color: "#964F4C" }}
                >
                  {formatPrice(lowestPrice)}
                </span>
              </div>
            </div>

            {/* Bottom spacer for sticky CTA */}
            <div style={{ height: 80 }} />
          </div>

          {/* Sticky bottom CTA */}
          <div
            className="fixed bottom-0 left-0 right-0 z-40 bg-bg"
            style={{
              maxWidth: 768,
              margin: "0 auto",
              padding: "12px 20px",
              borderTop: "1px solid #E5E1DA",
            }}
          >
            <div className="flex gap-sm">
              <button
                onClick={() => setSaved((v) => !v)}
                className="flex-1 rounded-xl font-semibold"
                style={{
                  height: 52,
                  fontSize: "15px",
                  border: "1.5px solid #964F4C",
                  color: saved ? "#FFFFFF" : "#964F4C",
                  backgroundColor: saved ? "#964F4C" : "transparent",
                  transition: "background-color 0.2s, color 0.2s",
                }}
              >
                {saved ? "♥ 저장됨" : "♡ 저장"}
              </button>
              <button
                className="flex-1 rounded-xl text-white font-semibold"
                style={{
                  height: 52,
                  fontSize: "15px",
                  backgroundColor: "#964F4C",
                }}
              >
                A vs B 비교
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
