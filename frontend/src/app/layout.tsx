import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "WonSense",
  description: "서울의 물가 감각을 외국인에게",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ko" className="h-full antialiased">
      <body className="min-h-full flex flex-col bg-brand-pale text-slate-900">{children}</body>
    </html>
  );
}
