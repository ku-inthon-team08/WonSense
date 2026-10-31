import { binsFor, ticksFor, type ScaleMode } from "@/lib/heatmap";
import { t } from "@/lib/strings";

export function HeatmapLegend({ mode }: { mode: ScaleMode }) {
  const bins = binsFor(mode);
  const ticks = ticksFor(mode);
  return (
    <div className="text-xs text-slate-600">
      <div className="mb-1 flex justify-between font-medium">
        <span>← {t.heatmapCheaper}</span>
        <span>{t.heatmapSeoulAvg}</span>
        <span>{t.heatmapPricier} →</span>
      </div>
      <ul className="grid grid-cols-7 gap-0.5" aria-label={t.heatmapLegendLabel}>
        {bins.map((b) => (
          <li key={b.label} className="h-3 rounded-sm" style={{ background: b.fill }} aria-label={b.label} />
        ))}
      </ul>
      {/* 눈금은 색 단계 사이 경계에 둔다 (단계 i와 i+1 사이 = 전체 너비의 (i+1)/7) */}
      <div className="relative mt-1 h-4" aria-hidden>
        {ticks.map((tick, i) => (
          <span
            key={tick}
            className="absolute -translate-x-1/2 tabular-nums"
            style={{ left: `${((i + 1) / 7) * 100}%` }}
          >
            {tick}
          </span>
        ))}
      </div>
    </div>
  );
}
