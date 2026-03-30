import type { Metadata } from "next";
import { Nanum_Myeongjo } from "next/font/google";
import "./globals.css";

const nanumMyeongjo = Nanum_Myeongjo({
  subsets: ["latin"],
  weight: ["400", "700", "800"],
  variable: "--font-display",
  display: "swap",
});

export const metadata: Metadata = {
  title: "ColorFit — AI 퍼스널컬러 패션 추천",
  description: "퍼스널컬러 기반 AI 패션 코디 추천 엔진",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko" className={nanumMyeongjo.variable}>
      <body>{children}</body>
    </html>
  );
}
