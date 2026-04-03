"use client";

/**
 * 데모 시연용 페이지 — 데스크톱에서 모바일 앱처럼 보이도록
 * 아이폰 프레임 안에 /feed를 iframe으로 표시
 *
 * 접속: http://localhost:3000/demo
 */

export default function DemoPage() {
  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: "#1A1714",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "40px 20px",
      }}
    >
      {/* 폰 프레임 */}
      <div
        style={{
          width: 390,
          height: 844,
          borderRadius: 44,
          border: "8px solid #333",
          overflow: "hidden",
          boxShadow: "0 20px 60px rgba(0,0,0,0.5), 0 0 0 2px #555",
          position: "relative",
          backgroundColor: "#F8F6F3",
        }}
      >
        {/* 노치 */}
        <div
          style={{
            position: "absolute",
            top: 0,
            left: "50%",
            transform: "translateX(-50%)",
            width: 160,
            height: 34,
            backgroundColor: "#333",
            borderRadius: "0 0 20px 20px",
            zIndex: 10,
          }}
        />

        {/* 앱 화면 */}
        <iframe
          src="/feed"
          style={{
            width: "100%",
            height: "100%",
            border: "none",
            borderRadius: 36,
          }}
        />
      </div>

      {/* 우측 정보 패널 */}
      <div
        style={{
          marginLeft: 60,
          color: "#F0EDE8",
          fontFamily: "var(--font-display), serif",
          maxWidth: 320,
        }}
      >
        <h1 style={{ fontSize: 36, fontWeight: 700, lineHeight: 1.2, margin: 0 }}>
          ColorFit
        </h1>
        <p style={{ fontSize: 16, color: "#8C8578", marginTop: 12, lineHeight: 1.6 }}>
          개인 취향을 반영해 전문가처럼 추천하고,
          <br />빠르게 결정하게 만드는 스타일 서비스
        </p>
        <div style={{ marginTop: 32, fontSize: 13, color: "#6B7F5E", lineHeight: 1.8 }}>
          <p>✓ 퍼스널컬러 기반 코디 추천</p>
          <p>✓ TPO별 맞춤 스타일링</p>
          <p>✓ 결정 이유 + 리스크 가드</p>
          <p>✓ 10초 안에 결정</p>
        </div>
      </div>
    </div>
  );
}
