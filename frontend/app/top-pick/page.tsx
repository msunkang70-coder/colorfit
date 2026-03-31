"use client";

import { useRouter } from "next/navigation";

export default function TopPickPage() {
  const router = useRouter();

  return (
    <div className="min-h-dvh bg-bg max-w-[768px] mx-auto flex flex-col items-center justify-center px-md">
      <p style={{ fontSize: "48px", lineHeight: 1 }}>★</p>
      <h2
        className="mt-lg"
        style={{ fontFamily: "var(--font-display)", fontSize: "22px", fontWeight: 700 }}
      >
        Top Pick
      </h2>
      <p className="mt-sm text-text-secondary text-center" style={{ fontSize: "14px" }}>
        준비 중이에요. AI가 엄선한 오늘의 추천을 곧 만나보세요.
      </p>
      <button
        onClick={() => router.push("/feed")}
        className="mt-xl px-lg py-sm rounded-xl text-white font-semibold"
        style={{ backgroundColor: "#964F4C", fontSize: "14px" }}
      >
        코디 피드로 돌아가기
      </button>
    </div>
  );
}
