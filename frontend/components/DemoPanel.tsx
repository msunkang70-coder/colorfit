"use client";

import { usePathname } from "next/navigation";

interface PageNote {
  title: string;
  subtitle?: string;
  points: string[];
}

const PAGES: Record<string, PageNote> = {
  "/": {
    title: "ColorFit",
    subtitle: "\"추천하지 않는다. 결정을 쉽게 만든다.\"",
    points: [
      "Vision: 옷 고르는 시간을 0으로 만든다",
      "",
      "문제 (Why):",
      "· 패션 추천 서비스 이탈률 60%+",
      "· 추천 10개 = 비교 10번 = 피로 = 이탈",
      "· 사용자가 원하는 건 \"골라줘\"",
      "",
      "해결 (How):",
      "→ Decision First — Top1만 제시, 리스트 없음",
      "→ Explain Why — 모든 추천에 근거 제공",
      "→ Compare When Needed — 비교는 선택적",
      "→ Measure Decisions — 결정 속도·확신 측정",
      "",
      "심리 설계 3층:",
      "· 1층: 선택 과부하 → Top1으로 해결",
      "· 2층: 신뢰 부족 → 축 기반 근거로 해결",
      "· 3층: 리스크 불안 → risk_guard로 해결",
      "",
      "핵심 기능:",
      "· 퍼스널컬러 12톤 × TPO 8종 매칭",
      "· 5축 스코어링 (TPO/핏/컬러/스타일/리스크)",
      "· Stylist Criteria — TPO별 전문가 판단 기준",
      "",
      "기술 스택:",
      "· Next.js 15 + React 19 + Framer Motion",
      "· FastAPI + Pydantic v2",
      "· 1,645개 코디 / v2 스코어 사전 계산",
      "",
      "시장 규모:",
      "· TAM ₩3.2조 / SAM ₩960억 / SOM ₩9.6억",
    ],
  },
  "/onboarding/step1": {
    title: "성별 선택",
    subtitle: "개인화의 시작점",
    points: [
      "성별에 따라 전체 추천 경험이 달라짐",
      "· 무드 옵션 6개가 성별별로 분기",
      "· 스타일 이미지 16장이 남녀 별도 제공",
      "· 추천 코디 풀이 성별로 완전 분리",
      "",
      "UX 설계:",
      "· 2택 구조 → 인지 부담 최소화",
      "· 선택 즉시 시각 피드백 (scale + check)",
      "· 건너뛰기 → 여성 기본값",
    ],
  },
  "/onboarding/step2": {
    title: "퍼스널컬러 진단",
    subtitle: "12톤 체계 기반 색감 매칭",
    points: [
      "4시즌 × 3톤 = 12톤 퍼스널컬러",
      "봄웜(라이트/브라이트/뮤트)",
      "여름쿨(라이트/소프트/뮤트)",
      "가을웜(딥/브라이트/뮤트)",
      "겨울쿨(딥/브라이트/라이트)",
      "",
      "자신의 톤을 모르면:",
      "→ 간이 진단 (언더톤 + 어울리는 색)",
      "",
      "이 톤이 추천에 미치는 영향:",
      "· v2 color 축 (20% 가중치)",
      "· 아이템 색상과 사용자 톤 매칭 점수",
    ],
  },
  "/onboarding/step3": {
    title: "TPO + 분위기",
    subtitle: "상황이 스타일을 결정한다",
    points: [
      "TPO 8종: 출근/면접/캠퍼스/데이트/주말/여행/행사/운동",
      "최대 3개 복수 선택",
      "",
      "TPO가 추천에 미치는 영향:",
      "· Hard Filter: TPO 불일치 코디 제거",
      "· v2 tpo 축 (30% 가중치 — 최대)",
      "· Stylist Criteria: TPO별 판단 기준 활성화",
      "",
      "분위기 6개 (성별 연동):",
      "여성: 미니멀/클래식/캐주얼/러블리/스트릿/에디토리얼",
      "남성: 미니멀/클래식/캐주얼/댄디/스트릿/아메카지",
    ],
  },
  "/onboarding/step4": {
    title: "예산 설정",
    subtitle: "가격 범위 Hard Filter",
    points: [
      "₩30,000 ~ ₩500,000 슬라이더",
      "Hard Filter: 예산 × 1.5 초과 코디 제거",
      "통과한 코디는 모두 예산 내로 간주",
      "",
      "설계 의도:",
      "· PE(가성비)를 독립 축에서 제거",
      "· 예산은 필터로 처리, 점수에서 제외",
      "· 사용자에게 가격 부담 없는 결과만 제시",
    ],
  },
  "/onboarding/step5": {
    title: "스타일 취향 분석",
    subtitle: "4라운드 이미지 선택",
    points: [
      "라운드 1: 무드 (미니멀/캐주얼/스트릿/댄디)",
      "라운드 2: 장르 (모던오피스/빈티지/스포티/클래식)",
      "라운드 3: 핏 (오버사이즈/레귤러핏/슬림핏)",
      "라운드 4: 컬러 (모노톤/뉴트럴/파스텔/비비드)",
      "",
      "남녀 별도 이미지 (각 16장)",
      "선택값 → style_seed_choices로 저장",
      "",
      "Soft Scoring에 반영:",
      "· TPO_STYLE_REINTERPRET으로 맥락 해석",
      "· 면접+캐주얼 → 미니멀/페미닌으로 재해석",
    ],
  },
  "/feed": {
    title: "Decision Mode",
    subtitle: "Top1 중심 — 결정을 돕는 구조",
    points: [
      "핵심 원칙: 추천이 아니라 결정",
      "· Top1 코디 + 전문가 판단 기준 제시",
      "· 비교 없이 납득 가능한 설명 구조",
      "",
      "5축 스코어링 v2:",
      "· TPO 적합도 (30%)",
      "· 컬러 조합 (20%)",
      "· 스타일 일관성 (20%)",
      "· 핏 적합도 (15%)",
      "· 리스크 감점 (-30~0)",
      "",
      "Reason 3파트:",
      "· core: 추천 이유 한 문장",
      "· risk_guard: 왜 안전한 선택인지",
      "· situation: 언제 입으면 좋은지",
      "",
      "Stylist Criteria Layer:",
      "· TPO별 전문가 판단 기준 (단정함/안정감 등)",
      "· TPO별 피해야 할 리스크 표시",
      "",
      "Explore Mode (보조):",
      "· 축 기반 다양성으로 Top3 선발",
      "· 탭하면 Decision Mode로 전환",
    ],
  },
};

export default function DemoPanel() {
  const pathname = usePathname();
  const note = PAGES[pathname] || PAGES["/feed"] || { title: "ColorFit", points: [] };

  return (
    <div className="demo-panel">
      {/* Header */}
      <div className="demo-header">
        <span className="demo-logo">ColorFit</span>
        <span className="demo-badge">DEMO</span>
      </div>

      {/* Title */}
      <div className="demo-title">{note.title}</div>
      {note.subtitle && (
        <div style={{ fontSize: "12px", color: "#964F4C", marginTop: "-12px", marginBottom: "14px", fontWeight: 500 }}>
          {note.subtitle}
        </div>
      )}

      {/* Points */}
      <div className="demo-list">
        {note.points.map((p, i) =>
          p === "" ? (
            <div key={i} style={{ height: "8px" }} />
          ) : p.startsWith("→") || p.startsWith("·") ? (
            <div key={i} style={{ fontSize: "12px", color: "#A09888", lineHeight: 1.6, paddingLeft: p.startsWith("·") ? "8px" : "4px" }}>
              {p}
            </div>
          ) : (
            <div key={i} style={{ fontSize: "12px", color: p.includes(":") ? "#F0EDE8" : "#A09888", fontWeight: p.includes(":") ? 600 : 400, lineHeight: 1.6, marginTop: "2px" }}>
              {p}
            </div>
          )
        )}
      </div>

      {/* Footer */}
      <div className="demo-footer">
        <div className="demo-tech">Next.js 15 · FastAPI · 5축 v2 스코어링 · 1,645 코디</div>
        <div className="demo-flow">
          {[
            { p: "/", l: "★" },
            { p: "/onboarding/step1", l: "1" },
            { p: "/onboarding/step2", l: "2" },
            { p: "/onboarding/step3", l: "3" },
            { p: "/onboarding/step4", l: "4" },
            { p: "/onboarding/step5", l: "5" },
            { p: "/feed", l: "F" },
          ].map((s) => (
            <span
              key={s.p}
              className={`demo-dot ${pathname === s.p ? "active" : ""}`}
            >
              {s.l}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
