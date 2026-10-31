import { HeatmapView } from "@/components/heatmap/HeatmapView";
import { PageShell } from "@/components/PageShell";
import { t } from "@/lib/strings";

export default function HeatmapPage() {
  return (
    <PageShell title={t.heatmapPageTitle} description={t.heatmapIntro}>
      <HeatmapView />
    </PageShell>
  );
}
