"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function OutfitDetailPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/feed");
  }, [router]);

  return (
    <div className="min-h-dvh bg-bg max-w-[768px] mx-auto flex items-center justify-center">
      <p className="text-text-secondary" style={{ fontSize: "14px" }}>
        피드로 이동 중...
      </p>
    </div>
  );
}
