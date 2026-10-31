"use client";

import Link from "next/link";
import { HeatmapView } from "@/components/heatmap/HeatmapView";
import { useT } from "@/lib/i18n";

export default function HeatmapPage() {
  const t = useT();
  return (
    <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-6">
      <Link href="/" className="text-sm text-brand">{t.home}</Link>
      <h1 className="mt-2 text-2xl font-bold">{t.heatmapPageTitle}</h1>
      <p className="mb-4 mt-1 text-sm text-slate-600">{t.heatmapIntro}</p>
      <HeatmapView />
    </main>
  );
}
