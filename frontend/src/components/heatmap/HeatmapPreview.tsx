"use client";

import Link from "next/link";
import { SeoulMap } from "@/components/heatmap/SeoulMap";
import { binsFor, getHeatmap } from "@/lib/heatmap";
import { useApi } from "@/lib/useApi";
import { useDistrictName, useT } from "@/lib/i18n";

// 범례에 보여줄 색 단계 (binsFor의 7단계 중 양 끝·가운데 위주 5개). 문구는 strings의 heatmapLegendSteps 순서와 같다.
const LEGEND_BINS = [0, 1, 3, 5, 6];

// 홈 ③ 카드: 전체 물가 지수 미니 지도 + 세로 범례. 데이터가 없으면 회색 지도만 보인다.
export function HeatmapPreview() {
  const t = useT();
  const dn = useDistrictName();
  const heatmap = useApi("heatmap:all", (signal) => getHeatmap(null, { signal }));
  const districts = heatmap.data?.districts ?? [];
  const top = districts[0];
  const bottom = districts[districts.length - 1];
  const bins = binsFor("overall");

  return (
    <Link href="/heatmap" className="block" aria-label={t.heatmapPageTitle}>
      <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center sm:gap-8">
        <div className="w-full max-w-64">
          <SeoulMap districts={districts} mode="overall" compact />
        </div>
        <ul className="grid grid-cols-2 gap-x-4 gap-y-2 rounded-2xl bg-brand-pale px-4 py-3 text-sm text-slate-700 sm:grid-cols-1">
          {LEGEND_BINS.map((b, i) => (
            <li key={b} className="flex items-center gap-2.5 whitespace-nowrap">
              <span aria-hidden className="h-3 w-3 rounded-full" style={{ background: bins[b].fill }} />
              {t.heatmapLegendSteps[i]}
            </li>
          ))}
        </ul>
      </div>
      {top && bottom && (
        <p className="mt-3 text-center text-sm text-slate-600">
          {t.heatmapPricier} <span className="font-semibold text-slate-900">{dn(top.name)}</span> · {t.heatmapCheaper}{" "}
          <span className="font-semibold text-slate-900">{dn(bottom.name)}</span>
        </p>
      )}
    </Link>
  );
}
