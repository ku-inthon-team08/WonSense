"use client";

import Link from "next/link";
import { SeoulMap } from "@/components/heatmap/SeoulMap";
import { getHeatmap } from "@/lib/heatmap";
import { useApi } from "@/lib/useApi";
import { t } from "@/lib/strings";

// 홈 ③ 카드: 전체 물가 지수 미니 지도. 데이터가 없으면 회색 지도만 보인다.
export function HeatmapPreview() {
  const heatmap = useApi("heatmap:all", (signal) => getHeatmap(null, { signal }));
  const districts = heatmap.data?.districts ?? [];
  const top = districts[0];
  const bottom = districts[districts.length - 1];

  return (
    <Link href="/heatmap" className="block" aria-label={t.heatmapPageTitle}>
      <div className="mx-auto max-w-56">
        <SeoulMap districts={districts} mode="overall" compact />
      </div>
      {top && bottom && (
        <p className="mt-1 text-center text-xs text-slate-600">
          {t.heatmapPricier} <span className="font-semibold text-slate-900">{top.name}</span> · {t.heatmapCheaper}{" "}
          <span className="font-semibold text-slate-900">{bottom.name}</span>
        </p>
      )}
    </Link>
  );
}
