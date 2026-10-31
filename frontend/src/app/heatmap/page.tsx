import Link from "next/link";
import { HeatmapView } from "@/components/heatmap/HeatmapView";
import { t } from "@/lib/strings";

export default function HeatmapPage() {
  return (
    <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-6">
      <Link href="/" className="text-sm text-brand">{t.home}</Link>
      <h1 className="mt-2 text-2xl font-bold">{t.heatmapPageTitle}</h1>
      <p className="mb-4 mt-1 text-sm text-slate-600">{t.heatmapIntro}</p>
      <HeatmapView />
    </main>
  );
}
