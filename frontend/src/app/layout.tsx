import type { Metadata } from "next";
import localFont from "next/font/local";

import { BackendWarmUp } from "@/components/BackendWarmUp";
import { LanguageToggle } from "@/components/LanguageToggle";
import "./globals.css";

// Pretendard (variable) for both Korean and Latin text, self-hosted from the npm package.
const pretendard = localFont({
  src: "../../node_modules/pretendard/dist/web/variable/woff2/PretendardVariable.woff2",
  weight: "45 920",
  display: "swap",
  variable: "--font-pretendard",
});

export const metadata: Metadata = {
  title: "WonSense",
  description: "서울의 물가 감각을 외국인에게",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ko" className={`${pretendard.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-brand-pale text-slate-900">
        <BackendWarmUp />
        <LanguageToggle />
        {children}
        <footer className="mt-auto py-6 text-center text-xs text-slate-500">
          Copyright 2026. 8sense All Rights Reserved.
        </footer>
      </body>
    </html>
  );
}
