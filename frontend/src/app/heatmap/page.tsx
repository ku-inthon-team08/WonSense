"use client";

import { HeatmapView } from "@/components/heatmap/HeatmapView";
import { PageShell } from "@/components/PageShell";
import { useT } from "@/lib/i18n";

export default function HeatmapPage() {
  const t = useT();
  return (
    <PageShell title={t.heatmapPageTitle} description={t.heatmapIntro}>
      <HeatmapView />
    </PageShell>
  );
}
