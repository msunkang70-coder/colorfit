"use client";

import { useState, useRef } from "react";
import { motion, useMotionValue, useTransform, PanInfo } from "framer-motion";

interface ReasonData {
  core: string;
  evidence: string;
  risk_guard: string;
}

interface OutfitCardProps {
  outfitId: string;
  imageUrl: string;
  totalPrice: number;
  itemCount: number;
  reasons: ReasonData | null;
  variant?: "full" | "compact";
  label?: string;
  onTap?: (outfitId: string) => void;
  onSaveToggle?: (outfitId: string) => void;
  onDislike?: (outfitId: string) => void;
  index?: number;
}

function formatPrice(price: number): string {
  return `₩${price.toLocaleString("ko-KR")}`;
}

const SWIPE_THRESHOLD = -100;

export default function OutfitCard({
  outfitId,
  imageUrl,
  totalPrice,
  itemCount,
  reasons,
  variant = "full",
  label,
  onTap,
  onSaveToggle,
  onDislike,
  index = 0,
}: OutfitCardProps) {
  const isCompact = variant === "compact";
  const [saved, setSaved] = useState(false);
  const [heartScale, setHeartScale] = useState(1);
  const [dismissed, setDismissed] = useState(false);
  const [showBigHeart, setShowBigHeart] = useState(false);
  const lastTapRef = useRef(0);

  const x = useMotionValue(0);
  const opacity = useTransform(x, [-200, 0], [0, 1]);

  const triggerSave = () => {
    if (!saved) {
      setSaved(true);
      setHeartScale(0.8);
      setTimeout(() => setHeartScale(1.4), 100);
      setTimeout(() => setHeartScale(1), 300);
      setShowBigHeart(true);
      setTimeout(() => setShowBigHeart(false), 600);
      onSaveToggle?.(outfitId);
    }
  };

  const handleHeartClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    const next = !saved;
    setSaved(next);
    setHeartScale(0.8);
    setTimeout(() => setHeartScale(1.2), 100);
    setTimeout(() => setHeartScale(1), 250);
    onSaveToggle?.(outfitId);
  };

  const handleClick = () => {
    if (isCompact) {
      onTap?.(outfitId);
      return;
    }
    const now = Date.now();
    if (now - lastTapRef.current < 300) {
      triggerSave();
      lastTapRef.current = 0;
    } else {
      lastTapRef.current = now;
      setTimeout(() => {
        lastTapRef.current = 0;
      }, 300);
    }
  };

  const handleDragEnd = (_: unknown, info: PanInfo) => {
    if (info.offset.x < SWIPE_THRESHOLD) {
      setDismissed(true);
      onDislike?.(outfitId);
    }
  };

  if (dismissed) return null;

  const core = reasons?.core ?? "추천 코디";
  const evidence = reasons?.evidence ?? "";
  const riskGuard = reasons?.risk_guard ?? "";

  // ── Compact variant ──
  if (isCompact) {
    return (
      <motion.article
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.08, duration: 0.3, ease: "easeOut" as const }}
        onClick={handleClick}
        className="cursor-pointer rounded-lg overflow-hidden"
        style={{ backgroundColor: "#F0EDE8", padding: 12 }}
      >
        <div className="flex gap-[12px]">
          {/* Thumbnail */}
          <div className="shrink-0 rounded-md overflow-hidden" style={{ width: 80, height: 100 }}>
            {imageUrl ? (
              <img src={imageUrl} alt={core} loading="lazy" width={80} height={100} className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full bg-surface flex items-center justify-center">
                <span className="text-text-tertiary" style={{ fontSize: "10px" }}>이미지</span>
              </div>
            )}
          </div>
          {/* Info */}
          <div className="flex-1 min-w-0">
            {label && (
              <span
                className="inline-block rounded-full mb-[4px]"
                style={{ fontSize: "10px", fontWeight: 600, padding: "2px 8px", backgroundColor: "#964F4C", color: "#fff" }}
              >
                {label}
              </span>
            )}
            <h4 className="text-primary truncate" style={{ fontSize: "14px", fontWeight: 600, lineHeight: 1.3 }}>
              {core}
            </h4>
            <p className="text-primary font-bold mt-[2px]" style={{ fontSize: "14px" }}>
              {formatPrice(totalPrice)}
            </p>
            {evidence && (
              <p className="mt-[4px] text-text-secondary truncate" style={{ fontSize: "12px", lineHeight: 1.4 }}>
                {evidence}
              </p>
            )}
          </div>
        </div>
      </motion.article>
    );
  }

  // ── Full variant (기존) ──
  return (
    <motion.article
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -300 }}
      transition={{
        delay: index * 0.1,
        duration: 0.4,
        ease: "easeOut" as const,
      }}
      style={{ x, opacity, padding: "0 20px", marginBottom: 20 }}
      drag="x"
      dragConstraints={{ left: 0, right: 0 }}
      dragElastic={0.3}
      onDragEnd={handleDragEnd}
      onClick={handleClick}
      className="w-full cursor-pointer"
    >
      {/* Label badge */}
      {label && (
        <span
          className="inline-block rounded-full mb-[8px]"
          style={{ fontSize: "11px", fontWeight: 600, padding: "3px 10px", backgroundColor: "#964F4C", color: "#fff" }}
        >
          {label}
        </span>
      )}

      {/* Image */}
      <div className="relative w-full rounded-lg overflow-hidden" style={{ aspectRatio: "3 / 4" }}>
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={core}
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

        {showBigHeart && (
          <motion.div
            initial={{ scale: 0, opacity: 1 }}
            animate={{ scale: 1.2, opacity: 0 }}
            transition={{ duration: 0.6, ease: "easeOut" as const }}
            className="absolute inset-0 flex items-center justify-center pointer-events-none"
          >
            <svg width="80" height="80" viewBox="0 0 24 24" fill="#964F4C" stroke="none">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
            </svg>
          </motion.div>
        )}

        <span
          className="absolute bottom-3 left-3 rounded-full text-white"
          style={{ fontSize: "11px", padding: "4px 10px", backgroundColor: "rgba(0,0,0,0.5)" }}
        >
          {itemCount}pcs
        </span>

        <button
          onClick={handleHeartClick}
          className="absolute top-3 right-3"
          aria-label={saved ? "저장 취소" : "저장"}
          style={{ transform: `scale(${heartScale})`, transition: "transform 0.15s" }}
        >
          <svg
            width="36" height="36" viewBox="0 0 24 24"
            fill={saved ? "#964F4C" : "none"}
            stroke={saved ? "#964F4C" : "#FFFFFF"}
            strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
          >
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
          </svg>
        </button>
      </div>

      {/* Core */}
      <h3
        className="mt-[12px] text-primary truncate"
        style={{ fontFamily: "var(--font-display)", fontSize: "16px", fontWeight: 700, lineHeight: 1.3 }}
      >
        {core}
      </h3>

      {/* Price */}
      <p className="mt-[4px] text-primary font-bold" style={{ fontSize: "15px" }}>
        {formatPrice(totalPrice)}
      </p>

      {/* Evidence */}
      {evidence && (
        <p className="mt-[6px] text-text-secondary" style={{ fontSize: "13px", lineHeight: 1.5 }}>
          {evidence}
        </p>
      )}

      {/* Risk Guard */}
      {riskGuard && (
        <p className="mt-[4px]" style={{ fontSize: "13px", lineHeight: 1.5, color: "#6B7F5E" }}>
          {riskGuard}
        </p>
      )}
    </motion.article>
  );
}
