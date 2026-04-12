"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import OutfitCard from "@/components/OutfitCard";
import { getOnboardingData, resetOnboarding } from "@/lib/onboarding-store";
import {
  postReaction,
  postMetrics,
  getMetricsQueue,
  clearMetricsQueue,
  exportMetricsCsv,
} from "@/lib/api";
import type { MetricsPayload } from "@/lib/api";
import { selectDiverseTop3, applyStyleFilter, checkStyleConsistency, getStyleExplanation, getStylistCriteria } from "@/lib/feed-utils";
import type { FeedOutfit, RankedOutfit, StyleCheck } from "@/lib/feed-utils";

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

interface FeedResponse {
  outfits: FeedOutfit[];
  total_count: number;
  page: number;
  has_next: boolean;
}

type FeedStatus = "idle" | "loading" | "error";

// ── 메인 컴포넌트 ──

export default function FeedPage() {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const profileRef = useRef(getOnboardingData());

  const [activeTpo, setActiveTpo] = useState("");
  const [budgetExpanded, setBudgetExpanded] = useState(false);
  const [budgetMin, setBudgetMin] = useState(30000);
  const [budgetMax, setBudgetMax] = useState(100000);
  const [status, setStatus] = useState<FeedStatus>("idle");
  const [toastMsg, setToastMsg] = useState<string | null>(null);
  const userId = useRef("");

  // 클라이언트 마운트 후 localStorage 읽기 (hydration 불일치 방지)
  useEffect(() => {
    const p = getOnboardingData();
    // 온보딩 미완료 시 온보딩으로 리다이렉트
    if (!p.tone_id || p.tpo_list.length === 0) {
      router.replace("/onboarding/step1");
      return;
    }
    profileRef.current = p;
    setBudgetMin(p.budget_min);
    setBudgetMax(p.budget_max);
    setMounted(true);
  }, [router]);

  // ── 결정 상태 ──
  const [decision, setDecision] = useState<FeedOutfit | null>(null);
  const [allOutfits, setAllOutfits] = useState<FeedOutfit[]>([]);
  const [top3, setTop3] = useState<RankedOutfit[]>([]);
  const [expandLevel, setExpandLevel] = useState(0); // 0=Decision, 1=Top3
  const [selectedRank, setSelectedRank] = useState(1);
  const expandedRef = useRef(false);
  const maxExpandLevelRef = useRef(0); // 세션 중 도달한 최대 확장 레벨

  // ── 측정용 ──
  const pageViewTsRef = useRef("");
  const sessionIdRef = useRef("");

  // ── 설문 상태 ──
  const [showSurvey, setShowSurvey] = useState(false);
  const [trustScore, setTrustScore] = useState(0);
  const [confidence, setConfidence] = useState<"" | "yes" | "no">("");
  const decisionClickTsRef = useRef("");
  const ttdRef = useRef(0);

  // TPO/예산/마운트 변경 시 자동 fetch — AbortController로 이전 요청 취소
  useEffect(() => {
    if (!mounted) return;

    const abortController = new AbortController();

    sessionIdRef.current = Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
    pageViewTsRef.current = new Date().toISOString();

    // 즉시 loading + 이전 결과 초기화
    setStatus("loading");
    setDecision(null);
    setAllOutfits([]);
    setTop3([]);
    setExpandLevel(0);
    setSelectedRank(1);
    expandedRef.current = false;
    maxExpandLevelRef.current = 0;

    const p = profileRef.current;
    const tpoParam = activeTpo || p.tpo_list.join(",");
    const params = new URLSearchParams({
      tone_id: p.tone_id,
      tpo: tpoParam,
      gender: p.gender,
      budget_min: String(budgetMin),
      budget_max: String(budgetMax),
      page: "1",
      page_size: "5",
    });

    fetch(`${API_BASE}/api/feed?${params}`, { signal: abortController.signal })
      .then((res) => {
        if (!res.ok) throw new Error(`${res.status}`);
        return res.json();
      })
      .then((data: FeedResponse) => {
        const tpo = activeTpo || profileRef.current.tpo_list[0] || "";
        const filtered = applyStyleFilter(data.outfits, tpo, profileRef.current.style_moods ?? []);
        setAllOutfits(filtered);
        setDecision(filtered[0] ?? null);
        setTop3(selectDiverseTop3(filtered));
        setStatus("idle");
      })
      .catch((err) => {
        if (err.name === "AbortError") return; // 취소된 요청 무시
        setStatus("error");
      });

    return () => abortController.abort(); // cleanup: 이전 요청 취소
  }, [activeTpo, budgetMin, budgetMax, mounted]);

  const handleTpoChange = (tpo: string) => {
    setActiveTpo(tpo);
  };

  const showToast = (msg: string) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(null), 2000);
  };

  const handleSaveToggle = (outfitId: string) => {
    postReaction({ user_id: userId.current, outfit_id: outfitId, reaction_type: "save" }).catch(() => {});
  };

  const handleDislike = (outfitId: string) => {
    showToast("관심없음");
    postReaction({ user_id: userId.current, outfit_id: outfitId, reaction_type: "dislike" }).catch(() => {});
  };

  // ── Explore Mode 진입 ──
  const handleExpand = () => {
    expandedRef.current = true;
    setExpandLevel(1);
    maxExpandLevelRef.current = Math.max(maxExpandLevelRef.current, 1);
  };

  // ── Explore Mode에서 카드 선택 → Decision Mode 복귀 ──
  const handleSelectFromExplore = (outfitId: string) => {
    const ranked = top3.find((r) => r.outfit.outfit_id === outfitId);
    if (ranked) {
      setDecision(ranked.outfit);
      setSelectedRank(ranked.rank);
    }
    setExpandLevel(0);
  };

  // ── CTA 클릭 → 설문 팝업 (구조 변경 금지) ──
  const handleDecide = () => {
    if (!decision) return;

    decisionClickTsRef.current = new Date().toISOString();
    const pageViewTime = new Date(pageViewTsRef.current).getTime();
    const clickTime = new Date(decisionClickTsRef.current).getTime();
    ttdRef.current = clickTime - pageViewTime;

    setTrustScore(0);
    setConfidence("");
    setShowSurvey(true);
  };

  // ── 설문 완료 or 스킵 → 로그 저장 + 외부 이동 (구조 변경 금지) ──
  const completeSurvey = (skipped: boolean) => {
    const payload: MetricsPayload = {
      session_id: sessionIdRef.current,
      outfit_id: decision?.outfit_id ?? "",
      page_view_ts: pageViewTsRef.current,
      decision_click_ts: decisionClickTsRef.current,
      ttd_ms: ttdRef.current,
      cta_clicked: true,
      trust_score: skipped ? 0 : trustScore,
      confidence: skipped ? "skip" : confidence || "skip",
      tone_id: profileRef.current.tone_id,
      tpo: activeTpo || profileRef.current.tpo_list.join(","),
      timestamp: new Date().toISOString(),
      expanded: expandedRef.current,
      expand_level: maxExpandLevelRef.current,
      selected_rank: selectedRank,
    };

    postMetrics(payload);
    setShowSurvey(false);

    const itemName = decision?.items[0]?.name || decision?.items[0]?.category || "패션";
    const searchUrl = `https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=0&ie=utf8&query=${encodeURIComponent(itemName + " 구매")}`;
    const newWindow = window.open(searchUrl, "_blank");
    if (!newWindow) {
      window.location.href = searchUrl;
    }

    showToast("결정 완료!");
  };

  // Explore에서 보여줄 compact 카드들 (Top1 제외)
  const exploreCards = top3.filter((r) => r.outfit.outfit_id !== decision?.outfit_id);
  const showExploreButton = expandLevel === 0 && allOutfits.length >= 2;

  return (
    <div className="feed-page">
      {/* BG — 성별에 따라 배경 이미지 분기 */}
      <div className={`feed-bg ${profileRef.current.gender === "male" ? "feed-bg-m" : "feed-bg-f"}`} />
      <div className="feed-overlay" />

      {/* Header */}
      <header style={{ position: "relative", zIndex: 30, padding: "10px 16px 8px", background: "rgba(20,18,16,0.92)", backdropFilter: "blur(16px)", WebkitBackdropFilter: "blur(16px)", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
          <span style={{ fontFamily: "var(--font-display)", fontSize: "15px", fontWeight: 800, color: "#fff", letterSpacing: "1px" }}>ColorFit</span>
          <button
            onClick={() => { resetOnboarding(); router.replace("/onboarding/step1"); }}
            style={{ fontSize: "10px", color: "rgba(255,255,255,0.5)", background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 20, padding: "4px 10px", cursor: "pointer" }}
          >
            다시 진단
          </button>
        </div>

        <div style={{ margin: "0 -16px", padding: "0 16px", overflowX: "auto", overflowY: "hidden", WebkitOverflowScrolling: "touch", scrollbarWidth: "none", msOverflowStyle: "none" }}>
          <div style={{ display: "flex", gap: 5, width: "max-content", paddingBottom: 2, paddingRight: 16 }}>
            {TPO_TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => handleTpoChange(tab.id)}
                className={`glass-chip${activeTpo === tab.id ? " on" : ""}`}
                style={{ fontSize: "11px", padding: "5px 12px", whiteSpace: "nowrap" }}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </header>

      <main style={{ position: "relative", zIndex: 1 }}>
        {status === "loading" && (
          <div className="px-[20px]">
            <div className="animate-pulse">
              <div className="w-full rounded-lg" style={{ aspectRatio: "3 / 4", backgroundColor: "#E0DCD7" }} />
              <div className="mt-3 h-4 w-2/3 rounded bg-[#E0DCD7]" />
              <div className="mt-2 h-3 w-1/3 rounded bg-[#E0DCD7]" />
              <div className="mt-2 h-3 w-full rounded bg-[#E0DCD7]" />
            </div>
          </div>
        )}

        {status === "error" && (
          <div className="flex flex-col items-center justify-center py-3xl">
            <p style={{ fontSize: "16px" }}>불러오지 못했어요</p>
            <button onClick={() => { setMounted(false); setTimeout(() => setMounted(true), 0); }} className="mt-md px-lg py-sm rounded-lg"
              style={{ fontSize: "14px", border: "1.5px solid #964F4C", color: "#964F4C" }}>
              다시 시도
            </button>
          </div>
        )}

        {status === "idle" && !decision && (
          <div className="flex flex-col items-center justify-center py-3xl">
            <p className="text-text-secondary" style={{ fontSize: "40px", lineHeight: 1 }}>👗</p>
            <p className="mt-md" style={{ fontSize: "16px" }}>조건에 맞는 코디가 없어요</p>
            <button
              onClick={() => { setActiveTpo(""); setBudgetMin(0); setBudgetMax(300000); }}
              className="mt-md px-lg py-sm rounded-lg text-white"
              style={{ fontSize: "14px", backgroundColor: "#964F4C" }}>
              필터를 변경해보세요
            </button>
          </div>
        )}

        {/* Decision */}
        {status === "idle" && decision && (
          <>
            <section className="px-[20px] mb-[12px]">
              <p style={{ fontFamily: "var(--font-display)", fontSize: "18px", color: "#C4726F", fontWeight: 700, letterSpacing: "-0.3px" }}>
                오늘의 스타일
              </p>
              {(() => {
                const tpo = activeTpo || profileRef.current.tpo_list[0] || "";
                const criteria = getStylistCriteria(tpo);
                const moods = profileRef.current.style_moods ?? [];
                const explain = getStyleExplanation(moods, tpo);
                return (
                  <>
                    <p style={{ fontSize: "12px", color: "#8C8578", marginTop: 2 }}>
                      {explain || criteria.expertComment}
                    </p>
                    <div style={{ display: "flex", gap: "4px", marginTop: "6px", flexWrap: "wrap" }}>
                      {criteria.priorities.map((p) => (
                        <span key={p} style={{ fontSize: "10px", fontWeight: 500, color: "#964F4C", backgroundColor: "rgba(150,79,76,0.06)", padding: "2px 8px", borderRadius: "10px" }}>
                          {p}
                        </span>
                      ))}
                    </div>
                  </>
                );
              })()}
            </section>

            <OutfitCard
              outfitId={decision.outfit_id}
              imageUrl={decision.items[0]?.image_url ?? ""}
              totalPrice={decision.total_price}
              itemCount={decision.items.length}
              reasons={decision.reasons}
              items={decision.items}
              variant="full"
              label={expandLevel === 0
                ? (selectedRank > 1 ? "대안 선택됨" : undefined)
                : "1위 추천"}
              userContext={(() => {
                const tpo = activeTpo || profileRef.current.tpo_list[0] || "";
                const c = getStylistCriteria(tpo);
                return c.decisionCue;
              })()}
              onSaveToggle={handleSaveToggle}
              onDislike={handleDislike}
              index={0}
            />

            {/* 스타일 적합도 */}
            {(() => {
              const tpo = activeTpo || profileRef.current.tpo_list[0] || "";
              const sc = checkStyleConsistency(decision, tpo);
              if (sc.conflict) {
                return (
                  <div className="mx-[20px] mb-[8px] rounded-lg px-[12px] py-[8px]"
                    style={{ backgroundColor: "rgba(160,120,48,0.08)", border: "1px solid rgba(160,120,48,0.2)" }}>
                    <p style={{ fontSize: "11px", color: "#A07830", fontWeight: 500 }}>
                      ⚠ {sc.conflict} — 스타일 조합을 확인해보세요
                    </p>
                  </div>
                );
              }
              if (sc.ratio >= 0.7) {
                return (
                  <div className="mx-[20px] mb-[8px] rounded-lg px-[12px] py-[6px]"
                    style={{ backgroundColor: "rgba(107,127,94,0.06)" }}>
                    <p style={{ fontSize: "11px", color: "#6B7F5E", fontWeight: 500 }}>
                      ✓ 스타일 일관성 {Math.round(sc.ratio * 100)}% — {sc.dominant === "formal" ? "포멀" : sc.dominant === "casual" ? "캐주얼" : sc.dominant === "sport" ? "스포티" : "통합"} 중심 구성
                    </p>
                  </div>
                );
              }
              return null;
            })()}

            {/* Explore Mode: compact 카드들 */}
            <AnimatePresence>
              {expandLevel >= 1 && exploreCards.length > 0 && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3, ease: "easeOut" as const }}
                  className="px-[20px] overflow-hidden"
                >
                  <p style={{ fontSize: "13px", fontWeight: 600, color: "rgba(255,255,255,0.85)", marginBottom: 4 }}>
                    같은 조건, 다른 강점
                  </p>
                  <p style={{ fontSize: "10px", color: "rgba(255,255,255,0.4)", marginBottom: 10 }}>
                    탭하면 이 코디로 전환돼요
                  </p>
                  <div className="flex flex-col gap-[8px]">
                    {exploreCards.map((ranked, i) => (
                      <div key={ranked.outfit.outfit_id}>
                        {ranked.diffDesc && (
                          <p style={{ fontSize: "10px", color: "#964F4C", fontWeight: 500, marginBottom: 4, marginLeft: 4 }}>
                            ↗ {ranked.diffDesc}
                          </p>
                        )}
                        <OutfitCard
                          outfitId={ranked.outfit.outfit_id}
                          imageUrl={ranked.outfit.items[0]?.image_url ?? ""}
                          totalPrice={ranked.outfit.total_price}
                          itemCount={ranked.outfit.items.length}
                          reasons={ranked.outfit.reasons}
                          variant="compact"
                          label={ranked.label}
                          onTap={handleSelectFromExplore}
                          index={i + 1}
                        />
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* CTA 영역 */}
            <div style={{ padding: "10px 18px 12px", position: "relative", zIndex: 20 }}>
              {/* 요약 카드 */}
              {(decision.reasons?.risk_guard || decision.reasons?.situation) && (
                <div style={{ background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 12, padding: "8px 12px", marginBottom: 10 }}>
                  {decision.reasons?.risk_guard && (
                    <p style={{ fontSize: "11px", lineHeight: 1.4, color: "rgba(140,180,130,0.9)", fontWeight: 500, textAlign: "center" }}>
                      🛡 {decision.reasons.risk_guard}
                    </p>
                  )}
                  {decision.reasons?.situation && (
                    <p style={{ fontSize: "10px", color: "rgba(255,255,255,0.4)", textAlign: "center", marginTop: 4 }}>
                      📍 {decision.reasons.situation}
                    </p>
                  )}
                </div>
              )}

              <motion.button
                onClick={handleDecide}
                whileTap={{ scale: 0.97 }}
                style={{ width: "100%", padding: "13px 0", borderRadius: 14, fontSize: 14, fontWeight: 600, color: "#fff", background: "linear-gradient(135deg, #7A3E3C, #964F4C, #B5605D)", border: "none", boxShadow: "0 4px 16px rgba(150,79,76,0.3)" }}
              >
                이 스타일로 선택
              </motion.button>
              {showExploreButton && (
                <button
                  onClick={handleExpand}
                  style={{ width: "100%", marginTop: 6, padding: "10px 0", fontSize: "11px", color: "rgba(255,255,255,0.4)", background: "none", border: "none", cursor: "pointer" }}
                >
                  {getStylistCriteria(activeTpo || profileRef.current.tpo_list[0] || "").exploreCta}
                </button>
              )}
            </div>
          </>
        )}
      </main>

      {/* 설문 팝업 — 다크 글래스모피즘 */}
      <AnimatePresence>
        {showSurvey && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-end justify-center"
            style={{ backgroundColor: "rgba(0,0,0,0.6)", backdropFilter: "blur(4px)" }}
            onClick={() => completeSurvey(true)}
          >
            <motion.div
              initial={{ y: 300 }}
              animate={{ y: 0 }}
              exit={{ y: 300 }}
              transition={{ type: "spring", damping: 28, stiffness: 320 }}
              className="w-full"
              style={{
                maxWidth: 393,
                padding: "20px 20px 32px",
                borderRadius: "20px 20px 0 0",
                background: "rgba(30,27,24,0.95)",
                backdropFilter: "blur(20px)",
                WebkitBackdropFilter: "blur(20px)",
                border: "1px solid rgba(255,255,255,0.08)",
                borderBottom: "none",
              }}
              onClick={(e) => e.stopPropagation()}
            >
              {/* 드래그 핸들 */}
              <div style={{ width: 36, height: 4, borderRadius: 2, background: "rgba(255,255,255,0.15)", margin: "0 auto 20px" }} />

              {/* 헤더 */}
              <p style={{ fontSize: "11px", fontWeight: 600, color: "#964F4C", letterSpacing: "1.5px", textTransform: "uppercase", marginBottom: 4 }}>
                Quick Survey
              </p>
              <p style={{ fontSize: "17px", fontWeight: 700, color: "rgba(240,237,232,0.9)", lineHeight: 1.3 }}>
                이 코디, 어떠셨나요?
              </p>
              <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.3)", marginTop: 4 }}>
                2개 질문 · 5초면 끝나요
              </p>

              {/* Q1: 신뢰도 */}
              <div style={{ marginTop: 20, padding: "16px", borderRadius: 14, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)" }}>
                <p style={{ fontSize: "13px", fontWeight: 600, color: "rgba(240,237,232,0.8)", marginBottom: 10 }}>
                  추천 신뢰도
                </p>
                <div className="flex gap-[6px]">
                  {[1, 2, 3, 4, 5].map((n) => (
                    <motion.button
                      key={n}
                      whileTap={{ scale: 0.92 }}
                      onClick={() => setTrustScore(n)}
                      className="flex-1 rounded-xl font-semibold"
                      style={{
                        padding: "12px 0",
                        fontSize: "15px",
                        backgroundColor: trustScore === n ? "#964F4C" : "rgba(255,255,255,0.06)",
                        color: trustScore === n ? "#FFFFFF" : "rgba(255,255,255,0.4)",
                        border: trustScore === n ? "1px solid rgba(150,79,76,0.5)" : "1px solid rgba(255,255,255,0.06)",
                        transition: "all 0.2s",
                      }}
                    >
                      {n}
                    </motion.button>
                  ))}
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", marginTop: 6 }}>
                  <span style={{ fontSize: "10px", color: "rgba(255,255,255,0.2)" }}>전혀 안 맞아요</span>
                  <span style={{ fontSize: "10px", color: "rgba(255,255,255,0.2)" }}>완벽해요</span>
                </div>
              </div>

              {/* Q2: 구매 확신 */}
              <div style={{ marginTop: 12, padding: "16px", borderRadius: 14, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)" }}>
                <p style={{ fontSize: "13px", fontWeight: 600, color: "rgba(240,237,232,0.8)", marginBottom: 10 }}>
                  이대로 입고 나갈 수 있나요?
                </p>
                <div className="flex gap-[8px]">
                  {([["yes", "네, 입을래요", "👍"], ["no", "아니요, 패스", "👎"]] as const).map(([val, label, emoji]) => (
                    <motion.button
                      key={val}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => setConfidence(val)}
                      className="flex-1 rounded-xl font-semibold"
                      style={{
                        padding: "14px 0",
                        fontSize: "14px",
                        backgroundColor: confidence === val
                          ? val === "yes" ? "rgba(107,127,94,0.25)" : "rgba(160,120,48,0.2)"
                          : "rgba(255,255,255,0.06)",
                        color: confidence === val
                          ? val === "yes" ? "rgba(140,180,130,0.9)" : "rgba(200,170,100,0.9)"
                          : "rgba(255,255,255,0.4)",
                        border: confidence === val
                          ? val === "yes" ? "1px solid rgba(107,127,94,0.35)" : "1px solid rgba(160,120,48,0.3)"
                          : "1px solid rgba(255,255,255,0.06)",
                        transition: "all 0.2s",
                      }}
                    >
                      <span style={{ marginRight: 4 }}>{emoji}</span>{label}
                    </motion.button>
                  ))}
                </div>
              </div>

              {/* 버튼 */}
              <div className="flex gap-[8px]" style={{ marginTop: 20 }}>
                <button
                  onClick={() => completeSurvey(true)}
                  className="flex-1 rounded-xl"
                  style={{
                    padding: "14px 0",
                    fontSize: "13px",
                    fontWeight: 500,
                    color: "rgba(255,255,255,0.35)",
                    background: "rgba(255,255,255,0.04)",
                    border: "1px solid rgba(255,255,255,0.08)",
                  }}
                >
                  건너뛰기
                </button>
                <motion.button
                  whileTap={{ scale: 0.97 }}
                  onClick={() => completeSurvey(false)}
                  className="flex-1 rounded-xl font-bold"
                  style={{
                    padding: "14px 0",
                    fontSize: "14px",
                    background: (trustScore > 0 || confidence)
                      ? "linear-gradient(135deg, #964F4C, #C4726F)"
                      : "rgba(150,79,76,0.3)",
                    color: "#FFFFFF",
                    border: "none",
                    boxShadow: (trustScore > 0 || confidence) ? "0 4px 16px rgba(150,79,76,0.3)" : "none",
                    transition: "all 0.2s",
                  }}
                >
                  제출하고 쇼핑몰 이동 →
                </motion.button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Toast */}
      <AnimatePresence>
        {toastMsg && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="fixed bottom-24 left-1/2 -translate-x-1/2 px-lg py-sm rounded-full z-50"
            style={{ backgroundColor: "rgba(34,34,34,0.85)", color: "#FFFFFF", fontSize: "14px" }}
          >
            {toastMsg}
          </motion.div>
        )}
      </AnimatePresence>

      {process.env.NODE_ENV !== "production" && <DebugPanel />}
    </div>
  );
}

// ── Debug Panel ──

function DebugPanel() {
  const [open, setOpen] = useState(false);
  const [queue, setQueue] = useState<MetricsPayload[]>([]);
  const refresh = () => setQueue(getMetricsQueue());
  useEffect(() => { if (open) refresh(); }, [open]);

  const handleTestLog = () => {
    postMetrics({
      session_id: "test_" + Date.now().toString(36), outfit_id: "test_outfit",
      page_view_ts: new Date().toISOString(), decision_click_ts: new Date().toISOString(),
      ttd_ms: Math.round(Math.random() * 20000), cta_clicked: true,
      trust_score: Math.ceil(Math.random() * 5),
      confidence: Math.random() > 0.5 ? "yes" : "no",
      tone_id: "spring_warm_light", tpo: "commute", timestamp: new Date().toISOString(),
      expanded: Math.random() > 0.5, expand_level: Math.floor(Math.random() * 2),
      selected_rank: Math.ceil(Math.random() * 3),
    });
    setTimeout(refresh, 100);
  };

  const handleCsvDownload = () => {
    const csv = exportMetricsCsv();
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `colorfit_metrics_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click(); URL.revokeObjectURL(url);
  };

  if (!open) {
    return (
      <button onClick={() => setOpen(true)} className="fixed top-2 right-2 z-[9999] rounded-full"
        style={{ fontSize: "10px", padding: "4px 8px", backgroundColor: "rgba(0,0,0,0.6)", color: "#fff" }}>
        DBG
      </button>
    );
  }

  const recent = queue.slice(-5).reverse();
  return (
    <div className="fixed top-0 right-0 z-[9999] overflow-auto"
      style={{ width: 320, maxHeight: "80vh", backgroundColor: "rgba(26,23,20,0.95)", color: "#F0EDE8", fontSize: "11px", padding: 12, borderRadius: "0 0 0 12px" }}>
      <div className="flex justify-between items-center mb-2">
        <span style={{ fontWeight: 700, fontSize: "13px" }}>Debug Panel</span>
        <button onClick={() => setOpen(false)} style={{ fontSize: "13px" }}>X</button>
      </div>
      <p>Queue: <strong>{queue.length}</strong></p>
      <div className="flex gap-1 mt-2 flex-wrap">
        <button onClick={refresh} style={dbgBtn}>Refresh</button>
        <button onClick={handleTestLog} style={dbgBtn}>+ Test</button>
        <button onClick={() => { clearMetricsQueue(); refresh(); }} style={{ ...dbgBtn, color: "#ff6b6b" }}>Clear</button>
        <button onClick={handleCsvDownload} style={dbgBtn}>CSV</button>
      </div>
      {recent.length > 0 && (
        <div className="mt-3">
          <p style={{ fontWeight: 600, marginBottom: 4 }}>Recent:</p>
          {recent.map((m, i) => (
            <div key={i} className="mb-2" style={{ padding: "4px 6px", backgroundColor: "rgba(255,255,255,0.08)", borderRadius: 4 }}>
              <div>TTD:<strong>{m.ttd_ms}ms</strong> T:{m.trust_score} C:{m.confidence} R:{m.selected_rank ?? 1}</div>
              <div style={{ color: "#8C8578" }}>{m.expanded ? "EXP" : "DEC"} L{m.expand_level ?? 0} | {m.session_id?.slice(0, 6)}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const dbgBtn: React.CSSProperties = {
  fontSize: "10px", padding: "3px 8px", borderRadius: 4,
  backgroundColor: "rgba(255,255,255,0.15)", color: "#F0EDE8", border: "none", cursor: "pointer",
};
