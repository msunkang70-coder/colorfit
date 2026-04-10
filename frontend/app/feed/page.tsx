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
import { selectDiverseTop3, applyStyleFilter, checkStyleConsistency, getStyleExplanation } from "@/lib/feed-utils";
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

    const mallUrl = decision?.items[0]?.mall_url;
    if (mallUrl) {
      const newWindow = window.open(mallUrl, "_blank");
      if (!newWindow) {
        window.location.href = mallUrl;
      }
    }

    showToast("결정 완료!");
  };

  // Explore에서 보여줄 compact 카드들 (Top1 제외)
  const exploreCards = top3.filter((r) => r.outfit.outfit_id !== decision?.outfit_id);
  const showExploreButton = expandLevel === 0 && allOutfits.length >= 2;

  return (
    <div className="min-h-dvh bg-bg max-w-[768px] mx-auto">
      {/* Header */}
      <header className="sticky top-0 z-30 bg-bg px-md pt-md pb-sm">
        <div className="flex items-center justify-between">
          <h1 className="brand-logo">ColorFit</h1>
          <div className="flex items-center gap-[8px]">
            <button
              className="px-[10px] py-[6px] rounded-full bg-surface text-text-secondary"
              style={{ fontSize: "11px" }}
              onClick={() => { resetOnboarding(); router.replace("/onboarding/step1"); }}
            >
              다시 설정
            </button>
            <button
              className="w-8 h-8 rounded-full bg-surface flex items-center justify-center"
              aria-label="프로필"
              onClick={() => router.push("/profile")}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                <circle cx="12" cy="7" r="4" />
              </svg>
            </button>
          </div>
        </div>

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
                border: activeTpo === tab.id ? "1.5px solid #964F4C" : "1.5px solid #E0DCD7",
                transition: "background-color 0.2s, color 0.2s",
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

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
              <div className="mt-sm pb-sm">
                <p className="text-text-tertiary mb-xs" style={{ fontSize: "11px" }}>최대 예산</p>
                <input type="range" min={30000} max={500000} step={10000} value={budgetMax}
                  onChange={(e) => setBudgetMax(Math.max(+e.target.value, 30000))}
                  className="w-full accent-accent" />
                <div className="flex justify-between text-text-tertiary" style={{ fontSize: "10px" }}>
                  <span>₩30,000</span>
                  <span>₩500,000</span>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </header>

      <main>
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
              <p style={{ fontFamily: "var(--font-display)", fontSize: "22px", color: "#964F4C", fontWeight: 700, letterSpacing: "-0.3px" }}>
                오늘의 결정
              </p>
              <p style={{ fontSize: "12px", color: "#8C8578", marginTop: 2 }}>
                {(() => {
                  const tpo = activeTpo || profileRef.current.tpo_list[0] || "";
                  const moods = profileRef.current.style_moods ?? [];
                  const explain = getStyleExplanation(moods, tpo);
                  if (explain) return explain;
                  if (moods.length > 0) return `${moods.slice(0, 2).join(" · ")} 취향 기반 추천`;
                  return "당신의 퍼스널컬러에 맞춘 코디예요";
                })()}
              </p>
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
              userContext={
                profileRef.current.style_moods.length > 0
                  ? `${profileRef.current.style_moods.join(" · ")} 선호 반영`
                  : undefined
              }
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
                  <p className="text-text-secondary mb-[4px]" style={{ fontSize: "13px", fontWeight: 600, color: "#222" }}>
                    같은 조건, 다른 강점
                  </p>
                  <p className="text-text-secondary mb-[10px]" style={{ fontSize: "11px" }}>
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

            {/* Risk Guard + CTA */}
            <div
              className="fixed bottom-[60px] left-0 right-0 z-20 px-[20px] pb-[12px] pt-[8px]"
              style={{ background: "linear-gradient(transparent, #F8F6F3 20%)", maxWidth: 768, margin: "0 auto" }}
            >
              {decision.reasons?.risk_guard && (
                <p className="text-center mb-[8px]" style={{ fontSize: "12px", lineHeight: 1.4, color: "#6B7F5E" }}>
                  ✓ {decision.reasons.risk_guard}
                </p>
              )}
              <button
                onClick={handleDecide}
                className="w-full cta-primary"
              >
                이 코디로 결정
              </button>
              {showExploreButton && (
                <button
                  onClick={handleExpand}
                  className="w-full mt-[6px] py-[14px] text-text-secondary"
                  style={{ fontSize: "13px" }}
                >
                  비슷한 선택 보기
                </button>
              )}
            </div>

            <div style={{ height: 140 }} />
          </>
        )}
      </main>

      {/* 설문 팝업 */}
      <AnimatePresence>
        {showSurvey && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-end justify-center"
            style={{ backgroundColor: "rgba(0,0,0,0.4)" }}
            onClick={() => completeSurvey(true)}
          >
            <motion.div
              initial={{ y: 300 }}
              animate={{ y: 0 }}
              exit={{ y: 300 }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="w-full rounded-t-2xl bg-bg"
              style={{ maxWidth: 768, padding: "24px 20px 32px" }}
              onClick={(e) => e.stopPropagation()}
            >
              <p style={{ fontSize: "15px", fontWeight: 600, color: "#222222" }}>
                이 코디를 얼마나 신뢰하나요?
              </p>
              <div className="flex gap-[8px] mt-[12px]">
                {[1, 2, 3, 4, 5].map((n) => (
                  <button
                    key={n}
                    onClick={() => setTrustScore(n)}
                    className="flex-1 py-[12px] rounded-lg font-semibold"
                    style={{
                      fontSize: "16px",
                      backgroundColor: trustScore === n ? "#964F4C" : "#F0EDE8",
                      color: trustScore === n ? "#FFFFFF" : "#222222",
                      transition: "background-color 0.15s, color 0.15s",
                    }}
                  >
                    {n}
                  </button>
                ))}
              </div>
              <p className="text-text-tertiary mt-[4px]" style={{ fontSize: "11px" }}>
                1 = 전혀 신뢰 안함 · 5 = 매우 신뢰
              </p>

              <p className="mt-[20px]" style={{ fontSize: "15px", fontWeight: 600, color: "#222222" }}>
                이대로 입을 것 같나요?
              </p>
              <div className="flex gap-[8px] mt-[12px]">
                {([["yes", "네"], ["no", "아니요"]] as const).map(([val, label]) => (
                  <button
                    key={val}
                    onClick={() => setConfidence(val)}
                    className="flex-1 py-[12px] rounded-lg font-semibold"
                    style={{
                      fontSize: "15px",
                      backgroundColor: confidence === val ? "#964F4C" : "#F0EDE8",
                      color: confidence === val ? "#FFFFFF" : "#222222",
                      transition: "background-color 0.15s, color 0.15s",
                    }}
                  >
                    {label}
                  </button>
                ))}
              </div>

              <div className="flex gap-[8px] mt-[24px]">
                <button
                  onClick={() => completeSurvey(true)}
                  className="flex-1 py-[12px] rounded-xl text-text-secondary"
                  style={{ fontSize: "14px", border: "1.5px solid #E5E1DA" }}
                >
                  건너뛰기
                </button>
                <button
                  onClick={() => completeSurvey(false)}
                  className="flex-1 py-[12px] rounded-xl text-white font-bold"
                  style={{ fontSize: "14px", backgroundColor: "#964F4C" }}
                >
                  제출하고 쇼핑몰 이동
                </button>
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
