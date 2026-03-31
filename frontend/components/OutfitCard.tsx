"use client";

import { useState } from "react";
import { motion } from "framer-motion";

interface OutfitScore {
  pcf: number;
  of: number;
}

interface OutfitCardProps {
  outfitId: string;
  imageUrl: string;
  title: string;
  totalPrice: number;
  itemCount: number;
  reason: string;
  scores: OutfitScore;
  isSaved?: boolean;
  onTap?: (outfitId: string) => void;
  onSaveToggle?: (outfitId: string) => void;
  index?: number;
}

function formatPrice(price: number): string {
  return `₩${price.toLocaleString("ko-KR")}`;
}

const SCORE_COLORS: Record<string, string> = {
  PCF: "#964F4C",
  OF: "#4F97A3",
};

export default function OutfitCard({
  outfitId,
  imageUrl,
  title,
  totalPrice,
  itemCount,
  reason,
  scores,
  isSaved: initialSaved = false,
  onTap,
  onSaveToggle,
  index = 0,
}: OutfitCardProps) {
  const [saved, setSaved] = useState(initialSaved);
  const [heartScale, setHeartScale] = useState(1);

  const handleSave = (e: React.MouseEvent) => {
    e.stopPropagation();
    setSaved((prev) => !prev);
    setHeartScale(0.8);
    setTimeout(() => setHeartScale(1.2), 100);
    setTimeout(() => setHeartScale(1), 250);
    onSaveToggle?.(outfitId);
  };

  const handleTap = () => {
    onTap?.(outfitId);
  };

  return (
    <motion.article
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        delay: index * 0.1,
        duration: 0.4,
        ease: "easeOut" as const,
      }}
      onClick={handleTap}
      className="w-full cursor-pointer"
      style={{ padding: "0 20px", marginBottom: 20 }}
    >
      {/* Image container */}
      <div className="relative w-full rounded-lg overflow-hidden" style={{ aspectRatio: "3 / 4" }}>
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={title}
            loading="lazy"
            width={400}
            height={533}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full bg-surface flex items-center justify-center">
            <span className="text-text-tertiary" style={{ fontSize: "13px" }}>
              이미지 없음
            </span>
          </div>
        )}

        {/* Item count badge — bottom left */}
        <span
          className="absolute bottom-3 left-3 rounded-full text-white"
          style={{
            fontSize: "11px",
            padding: "4px 10px",
            backgroundColor: "rgba(0, 0, 0, 0.5)",
          }}
        >
          {itemCount}pcs
        </span>

        {/* Heart icon — top right */}
        <button
          onClick={handleSave}
          className="absolute top-3 right-3"
          aria-label={saved ? "저장 취소" : "저장"}
          style={{ transform: `scale(${heartScale})`, transition: "transform 0.15s" }}
        >
          <svg
            width="36"
            height="36"
            viewBox="0 0 24 24"
            fill={saved ? "#964F4C" : "none"}
            stroke={saved ? "#964F4C" : "#FFFFFF"}
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
          </svg>
        </button>
      </div>

      {/* Title */}
      <h3
        className="mt-[12px] text-primary truncate"
        style={{
          fontFamily: "var(--font-display)",
          fontSize: "16px",
          fontWeight: 700,
          lineHeight: 1.3,
        }}
      >
        {title}
      </h3>

      {/* Price */}
      <p
        className="mt-[4px] text-primary font-bold"
        style={{ fontSize: "15px" }}
      >
        {formatPrice(totalPrice)}
      </p>

      {/* Reason */}
      {reason && (
        <p
          className="mt-[4px] text-text-secondary truncate"
          style={{ fontSize: "13px" }}
        >
          {reason}
        </p>
      )}

      {/* Score badges */}
      <div className="flex gap-[6px] mt-[8px]">
        {(
          [
            ["PCF", scores.pcf],
            ["OF", scores.of],
          ] as const
        ).map(([label, value]) => (
          <span
            key={label}
            className="rounded-full"
            style={{
              fontSize: "11px",
              padding: "2px 8px",
              backgroundColor: "#F0EDE8",
              color: SCORE_COLORS[label],
              fontWeight: 600,
            }}
          >
            {label} {Math.round(value)}
          </span>
        ))}
      </div>
    </motion.article>
  );
}
