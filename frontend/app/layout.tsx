import type { Metadata } from "next";
import { Nanum_Myeongjo } from "next/font/google";
import "./globals.css";
import BottomTabBar from "@/components/BottomTabBar";
import DemoPanel from "@/components/DemoPanel";

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

const isDemo = process.env.NEXT_PUBLIC_DEMO_MODE === "true";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko" className={nanumMyeongjo.variable}>
      <head>
        <meta name="referrer" content="no-referrer" />
      </head>
      <body>
        {isDemo ? (
          <div className="demo-wrapper">
            <div id="app-frame" className="app-frame">
              {children}
              <BottomTabBar />
            </div>
            <DemoPanel />
          </div>
        ) : (
          <div className="prod-wrapper">
            {children}
            <BottomTabBar />
          </div>
        )}
      </body>
    </html>
  );
}
