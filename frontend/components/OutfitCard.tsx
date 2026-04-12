"use client";

import { useState, useRef } from "react";
import { motion, useMotionValue, useTransform, PanInfo, AnimatePresence } from "framer-motion";

interface ReasonData {
  core: string;
  evidence: string;
  risk_guard: string;
}

interface OutfitItem {
  image_url: string;
  name: string;
  price: number;
  category?: string;
  brand?: string;
  mall_url?: string;
  style_tag?: string;
  formality?: number;
}

function getItemUrl(item: OutfitItem): string {
  // 직접 링크가 있으면 그대로 사용 (smartstore, coupang 등)
  const url = item.mall_url || "";
  if (url && !url.includes("search.shopping.naver") && !url.includes("search.naver.com") && url.startsWith("http")) {
    return url;
  }
  // fallback: 상품명 기반 네이버 쇼핑 검색
  const name = item.name || item.category || "패션";
  const cat = item.category || "";
  const query = cat ? `${cat} ${name.slice(0, 30)}` : name.slice(0, 30);
  return `https://search.shopping.naver.com/search/all?query=${encodeURIComponent(query)}&cat_id=&frm=NVSHATC`;
}

interface OutfitCardProps {
  outfitId: string;
  imageUrl: string;
  totalPrice: number;
  itemCount: number;
  reasons: ReasonData | null;
  items?: OutfitItem[];
  variant?: "full" | "compact";
  label?: string;
  /** 사용자 선택 기반 추천 맥락 (프론트 보강용) */
  userContext?: string;
  onTap?: (outfitId: string) => void;
  onSaveToggle?: (outfitId: string) => void;
  onDislike?: (outfitId: string) => void;
  index?: number;
}

function formatPrice(price: number): string {
  return `₩${price.toLocaleString("ko-KR")}`;
}

const SWIPE_THRESHOLD = -100;

const CATEGORY_ROLE: Record<string, string> = {
  "셔츠": "상의", "블라우스": "상의", "니트": "상의", "맨투맨": "상의",
  "후드": "상의", "티셔츠": "상의", "반팔티": "상의", "크롭탑": "상의",
  "슬랙스": "하의", "청바지": "하의", "반바지": "하의", "조거팬츠": "하의",
  "트레이닝팬츠": "하의", "스커트": "하의", "레깅스": "하의",
  "자켓": "아우터", "코트": "아우터", "바람막이": "아우터", "가디건": "아우터", "패딩": "아우터",
  "스니커즈": "신발", "로퍼": "신발", "힐": "신발", "플랫슈즈": "신발",
  "원피스": "원피스", "모자": "액세서리", "넥타이": "액세서리",
};

export default function OutfitCard({
  outfitId,
  imageUrl,
  totalPrice,
  itemCount,
  reasons,
  items,
  variant = "full",
  label,
  userContext,
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
  const [selectedItem, setSelectedItem] = useState<OutfitItem | null>(null);
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
      setTimeout(() => { lastTapRef.current = 0; }, 300);
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
  const riskGuard = (reasons as Record<string, string> | null)?.risk_guard ?? "";
  const situation = (reasons as Record<string, string> | null)?.situation ?? "";
  const computedTotal = items?.reduce((s, it) => s + (it.price ?? 0), 0) ?? 0;
  const displayTotal = computedTotal > 0 ? computedTotal : totalPrice;

  // ── Compact variant ──
  if (isCompact) {
    return (
      <motion.article
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.08, duration: 0.3, ease: "easeOut" as const }}
        onClick={handleClick}
        className="cursor-pointer rounded-xl overflow-hidden"
        style={{ backgroundColor: "rgba(255,255,255,0.06)", backdropFilter: "blur(8px)", WebkitBackdropFilter: "blur(8px)", border: "1px solid rgba(255,255,255,0.08)", padding: 12 }}
      >
        <div className="flex gap-[12px]">
          <div className="shrink-0 rounded-md overflow-hidden" style={{ width: 80, height: 100 }}>
            {imageUrl ? (
              <img src={imageUrl} alt={core} loading="lazy" width={80} height={100} className="w-full h-full object-cover" referrerPolicy="no-referrer" />
            ) : (
              <div className="w-full h-full bg-surface flex items-center justify-center">
                <span className="text-text-tertiary" style={{ fontSize: "10px" }}>이미지</span>
              </div>
            )}
          </div>
          <div className="flex-1 min-w-0">
            {label && (
              <span
                className="inline-block rounded-full mb-[4px]"
                style={{ fontSize: "10px", fontWeight: 600, padding: "2px 8px", backgroundColor: "#964F4C", color: "#fff" }}
              >
                {label}
              </span>
            )}
            <h4 className="truncate" style={{ fontSize: "13px", fontWeight: 600, lineHeight: 1.3, color: "rgba(255,255,255,0.9)" }}>
              {core}
            </h4>
            <p className="font-bold mt-[2px]" style={{ fontSize: "13px", color: "#fff" }}>
              {formatPrice(displayTotal)}
              <span style={{ fontSize: "9px", fontWeight: 400, color: "rgba(255,255,255,0.4)", marginLeft: 4 }}>
                {itemCount}pcs
              </span>
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

  // ── Full variant ──
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -300 }}
      transition={{ delay: index * 0.1, duration: 0.4, ease: "easeOut" as const }}
      style={{ padding: "0 20px", marginBottom: 20 }}
      className="w-full"
    >
    {/* 드래그 가능 영역: 이미지만 */}
    <motion.article
      style={{ x, opacity }}
      drag="x"
      dragConstraints={{ left: 0, right: 0 }}
      dragElastic={0.3}
      onDragEnd={handleDragEnd}
      onClick={handleClick}
      className="w-full cursor-pointer"
    >
      {/* Image — 룩북 스타일 */}
      <div className="relative w-full rounded-2xl overflow-hidden" style={{ aspectRatio: "3 / 4" }}>
        {label && (
          <span
            className="absolute top-[10px] left-[10px] z-10 rounded-full"
            style={{ fontSize: "10px", fontWeight: 600, padding: "3px 10px", backgroundColor: "rgba(0,0,0,0.5)", color: "#fff", backdropFilter: "blur(8px)" }}
          >
            {label}
          </span>
        )}
        {imageUrl ? (
          <img src={imageUrl} alt={core} loading="lazy" width={400} height={533}
            className="w-full h-full object-cover" referrerPolicy="no-referrer" />
        ) : (
          <div className="w-full h-full bg-surface flex items-center justify-center">
            <span className="text-text-tertiary" style={{ fontSize: "13px" }}>이미지 없음</span>
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

        {/* 오버레이 — 미니멀 */}
        <div
          className="absolute bottom-0 left-0 right-0 px-[14px] pb-[12px] pt-[48px]"
          style={{ background: "linear-gradient(transparent 0%, rgba(0,0,0,0.6) 100%)" }}
        >
          <h3 className="text-white" style={{ fontFamily: "var(--font-display)", fontSize: "15px", fontWeight: 700, lineHeight: 1.35, textShadow: "0 1px 3px rgba(0,0,0,0.4)" }}>
            {core}
          </h3>
          {userContext && (
            <p style={{ fontSize: "10px", color: "rgba(255,255,255,0.65)", marginTop: 2 }}>
              {userContext}
            </p>
          )}
          <p className="text-white font-bold mt-[4px]" style={{ fontSize: "17px", textShadow: "0 1px 3px rgba(0,0,0,0.4)" }}>
            {formatPrice(displayTotal)}
            <span style={{ fontSize: "10px", fontWeight: 400, opacity: 0.6, marginLeft: 4 }}>{itemCount}pcs</span>
          </p>
        </div>

        <button
          onClick={handleHeartClick}
          className="absolute top-3 right-3"
          aria-label={saved ? "저장 취소" : "저장"}
          style={{ transform: `scale(${heartScale})`, transition: "transform 0.15s" }}
        >
          <svg width="36" height="36" viewBox="0 0 24 24"
            fill={saved ? "#964F4C" : "none"} stroke={saved ? "#964F4C" : "#FFFFFF"}
            strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
          </svg>
        </button>
      </div>
    </motion.article>

      {/* ── 코디 구성 아이템 (드래그 밖, 독립 클릭 영역) ── */}
      {items && items.length > 1 && (
        <div className="mt-[12px] rounded-xl" style={{ backgroundColor: "rgba(255,255,255,0.06)", backdropFilter: "blur(8px)", border: "1px solid rgba(255,255,255,0.08)", padding: "12px", position: "relative", zIndex: 10, opacity: 1 }}>
          <div className="flex items-center justify-between mb-[8px]">
            <p style={{ fontSize: "12px", fontWeight: 600, color: "rgba(255,255,255,0.85)" }}>
              아이템 구성 {items.length}pcs
            </p>
            <p style={{ fontSize: "9px", color: "rgba(255,255,255,0.35)" }}>
              탭하여 상세보기
            </p>
          </div>

          {/* 아이템 리스트 */}
          <div className="flex flex-col gap-[6px]">
            {items.map((it, i) => {
              const catName = it.category || it.name.slice(0, 4);
              const role = CATEGORY_ROLE[catName] ?? "";
              const itemPrice = it.price ?? 0;
              return (
                <button
                  key={i}
                  onClick={(e) => { e.stopPropagation(); setSelectedItem(it); }}
                  className="flex items-center gap-[10px] rounded-lg w-full text-left"
                  style={{
                    padding: "8px",
                    backgroundColor: "rgba(255,255,255,0.04)",
                    border: "1px solid rgba(255,255,255,0.08)",
                    cursor: "pointer",
                    borderRadius: "10px",
                    transition: "border-color 0.15s, background-color 0.15s, transform 0.1s",
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.borderColor = "rgba(150,79,76,0.5)"; e.currentTarget.style.backgroundColor = "rgba(255,255,255,0.08)"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.08)"; e.currentTarget.style.backgroundColor = "rgba(255,255,255,0.04)"; }}
                  onMouseDown={(e) => { e.currentTarget.style.transform = "scale(0.98)"; }}
                  onMouseUp={(e) => { e.currentTarget.style.transform = "scale(1)"; }}
                >
                  <div className="shrink-0 rounded-md overflow-hidden" style={{ width: 44, height: 44 }}>
                    <img src={it.image_url} alt={catName} width={44} height={44}
                      className="w-full h-full object-cover" referrerPolicy="no-referrer" loading="lazy" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-[4px]">
                      {role && (
                        <span style={{ fontSize: "9px", fontWeight: 600, color: "#964F4C", backgroundColor: "rgba(150,79,76,0.08)", padding: "1px 5px", borderRadius: 4 }}>
                          {role}
                        </span>
                      )}
                      <span style={{ fontSize: "11px", fontWeight: 600, color: "rgba(255,255,255,0.85)" }}>{catName}</span>
                    </div>
                    {it.brand && (
                      <p style={{ fontSize: "10px", color: "#8C8578", marginTop: 1 }} className="truncate">{it.brand}</p>
                    )}
                  </div>
                  <div className="shrink-0 text-right">
                    {itemPrice > 0 && (
                      <p style={{ fontSize: "11px", fontWeight: 700, color: "#fff" }}>{formatPrice(itemPrice)}</p>
                    )}
                  </div>
                </button>
              );
            })}
          </div>

          {/* 합산 확인 */}
          {computedTotal > 0 && (
            <div className="flex justify-end items-center mt-[8px] pt-[8px]" style={{ borderTop: "1px solid rgba(255,255,255,0.08)" }}>
              <span style={{ fontSize: "10px", color: "rgba(255,255,255,0.4)", marginRight: 8 }}>합산</span>
              <span style={{ fontSize: "13px", fontWeight: 700, color: "#C4726F" }}>{formatPrice(computedTotal)}</span>
            </div>
          )}
        </div>
      )}

      {/* 전문가 코멘트 */}
      {(evidence || riskGuard) && (
        <div className="mt-[10px] rounded-xl" style={{ padding: "10px 12px", backgroundColor: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)" }}>
          {evidence && (
            <p style={{ fontSize: "11px", lineHeight: 1.5, color: "rgba(255,255,255,0.75)", fontWeight: 500 }}>
              💡 {evidence}
            </p>
          )}
          {riskGuard && (
            <p style={{ fontSize: "10px", lineHeight: 1.5, color: "rgba(107,127,94,0.9)", marginTop: evidence ? 4 : 0 }}>
              🛡 {riskGuard}
            </p>
          )}
          {situation && (
            <p style={{ fontSize: "9px", color: "rgba(255,255,255,0.35)", marginTop: 4 }}>
              📍 {situation}
            </p>
          )}
        </div>
      )}

      {/* ── 아이템 상세 하단 시트 ── */}
      <AnimatePresence>
        {selectedItem && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-50 flex items-end justify-center"
            style={{ backgroundColor: "rgba(0,0,0,0.45)" }}
            onClick={(e) => { e.stopPropagation(); setSelectedItem(null); }}
          >
            <motion.div
              initial={{ y: "100%" }}
              animate={{ y: 0 }}
              exit={{ y: "100%" }}
              transition={{ type: "spring", stiffness: 400, damping: 35 }}
              className="w-full rounded-t-2xl overflow-hidden"
              style={{ maxWidth: 768, backgroundColor: "#F8F6F3", maxHeight: "75vh" }}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Handle */}
              <div className="flex justify-center pt-[10px] pb-[4px]">
                <div style={{ width: 36, height: 4, borderRadius: 2, backgroundColor: "#E5E1DA" }} />
              </div>

              <div className="px-[24px] pb-[32px]">
                <div className="flex gap-[16px] mt-[8px]">
                  {/* 이미지 */}
                  <div className="shrink-0 rounded-xl overflow-hidden" style={{ width: 140, height: 140, border: "1px solid #E5E1DA" }}>
                    <img src={selectedItem.image_url} alt={selectedItem.category || selectedItem.name}
                      width={140} height={140} className="w-full h-full object-cover" referrerPolicy="no-referrer" />
                  </div>

                  {/* 정보 */}
                  <div className="flex-1 min-w-0 flex flex-col justify-center">
                    <div className="flex items-center gap-[6px]">
                      {selectedItem.category && CATEGORY_ROLE[selectedItem.category] && (
                        <span style={{ fontSize: "10px", fontWeight: 600, color: "#964F4C", backgroundColor: "rgba(150,79,76,0.08)", padding: "2px 6px", borderRadius: 4 }}>
                          {CATEGORY_ROLE[selectedItem.category]}
                        </span>
                      )}
                      <span style={{ fontSize: "12px", color: "#8C8578" }}>{selectedItem.category}</span>
                    </div>
                    <h3 className="mt-[4px]" style={{ fontSize: "16px", fontWeight: 700, color: "#222", lineHeight: 1.4 }}>
                      {selectedItem.name || selectedItem.category || "상품"}
                    </h3>
                    {selectedItem.brand && (
                      <p style={{ fontSize: "12px", color: "#8C8578", marginTop: 2 }}>{selectedItem.brand}</p>
                    )}
                    {(selectedItem.price ?? 0) > 0 && (
                      <p style={{ fontSize: "22px", fontWeight: 700, color: "#964F4C", marginTop: 8 }}>
                        {formatPrice(selectedItem.price)}
                      </p>
                    )}
                  </div>
                </div>

                {/* 코디 내 역할 + 스타일 정보 */}
                {selectedItem.category && (
                  <div className="mt-[12px]" style={{ backgroundColor: "#F0EDE8", padding: "10px 12px", borderRadius: 8 }}>
                    <p style={{ fontSize: "12px", color: "#8C8578", lineHeight: 1.5 }}>
                      이 코디에서 <strong style={{ color: "#222" }}>{CATEGORY_ROLE[selectedItem.category] || selectedItem.category}</strong> 역할을 합니다.
                      전체 코디 가격 {formatPrice(displayTotal)} 중 {(selectedItem.price ?? 0) > 0 ? `${Math.round(((selectedItem.price ?? 0) / displayTotal) * 100)}%` : "—"}를 차지해요.
                    </p>
                    <div className="flex gap-[6px] mt-[6px]">
                      {selectedItem.style_tag && (
                        <span style={{ fontSize: "10px", fontWeight: 600, color: "#964F4C", backgroundColor: "rgba(150,79,76,0.08)", padding: "2px 8px", borderRadius: 10 }}>
                          {selectedItem.style_tag}
                        </span>
                      )}
                      {(selectedItem.formality ?? 0) > 0 && (
                        <span style={{ fontSize: "10px", fontWeight: 600, color: "#6B7F5E", backgroundColor: "rgba(107,127,94,0.08)", padding: "2px 8px", borderRadius: 10 }}>
                          격식 {selectedItem.formality}/5
                        </span>
                      )}
                    </div>
                  </div>
                )}

                {/* 버튼 */}
                <div className="flex gap-[8px] mt-[16px]">
                  <button
                    onClick={(e) => { e.stopPropagation(); setSelectedItem(null); }}
                    className="flex-1 rounded-xl"
                    style={{ height: 48, fontSize: "14px", fontWeight: 600, backgroundColor: "#E5E1DA", color: "#222" }}
                  >
                    닫기
                  </button>
                  <a
                    href={getItemUrl(selectedItem)}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="flex-1 rounded-xl flex items-center justify-center"
                    style={{ height: 48, fontSize: "14px", fontWeight: 600, backgroundColor: "#964F4C", color: "#fff", textDecoration: "none" }}
                  >
                    상품 보러가기 →
                  </a>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
