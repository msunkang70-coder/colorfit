"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getOnboardingData } from "@/lib/onboarding-store";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const data = getOnboardingData();
    const isCompleted = data.tone_id && data.tpo_list.length > 0;
    if (isCompleted) {
      router.replace("/feed");
    } else {
      router.replace("/onboarding/step1");
    }
  }, [router]);

  return (
    <main className="flex min-h-dvh flex-col items-center justify-center bg-bg">
      <h1 className="text-4xl font-bold text-accent">ColorFit</h1>
      <p className="mt-4 text-body text-text-secondary">잠시만 기다려주세요...</p>
    </main>
  );
}
