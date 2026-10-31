"use client";

import { useState } from "react";
import { DistrictPanel } from "@/components/heatmap/DistrictPanel";
import { HeatmapLegend } from "@/components/heatmap/HeatmapLegend";
import { SeoulMap } from "@/components/heatmap/SeoulMap";
import { formatKrw } from "@/lib/format";
import { binFor, formatPct, getHeatmap, getHeatmapItems } from "@/lib/heatmap";
import { useApi } from "@/lib/useApi";
import { useDistrictName, useT } from "@/lib/i18n";

export function HeatmapView() {
  const t = useT();
  const dn = useDistrictName();
  const [itemId, setItemId] = useState<number | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  const items = useApi("heatmap-items", (signal) => getHeatmapItems({ signal }));
  const heatmap = useApi(`heatmap:${itemId ?? "all"}`, (signal) => getHeatmap(itemId, { signal }));

  const mode = itemId == null ? "overall" : "item";
  const item = items.data?.items.find((i) => i.item_id === itemId) ?? null;
  const districts = heatmap.data?.districts ?? [];
  const selectedDistrict = districts.find((d) => d.region === selected) ?? null;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <label htmlFor="heatmap-item" className="text-sm font-medium text-slate-700">
          {t.heatmapItemLabel}
        </label>
        <select
          id="heatmap-item"
          value={itemId ?? ""}
          onChange={(e) => setItemId(e.target.value ? Number(e.target.value) : null)}
          disabled={!items.data}
          className="min-w-0 flex-1 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm sm:max-w-xs"
        >
          <option value="">{t.heatmapAllItems}</option>
          {items.data?.items.map((i) => (
            <option key={i.item_id} value={i.item_id}>
              {i.name} ({formatKrw(i.seoul_avg)})
            </option>
          ))}
        </select>
      </div>

      <div className="grid gap-4 md:grid-cols-5">
        <section className="self-start rounded-2xl bg-white p-4 shadow-card md:col-span-3">
          {heatmap.error ? (
            <p className="py-16 text-center text-sm text-red-700">{t.heatmapError}</p>
          ) : (
            <div className={heatmap.loading ? "opacity-50 transition-opacity" : "transition-opacity"} aria-busy={heatmap.loading}>
              <SeoulMap districts={districts} mode={mode} selected={selected} onSelect={setSelected} />
            </div>
          )}
          <div className="mt-3">
            <HeatmapLegend mode={mode} />
          </div>
          <p className="mt-3 text-xs text-slate-500">
            {t.heatmapSourceDetail}
            {heatmap.data && ` · ${t.heatmapReferenceDate} ${heatmap.data.reference_date}`}
          </p>
        </section>

        <div className="flex flex-col gap-4 md:col-span-2">
          {selectedDistrict && (
            <DistrictPanel
              key={selectedDistrict.region}
              district={selectedDistrict}
              item={item}
              onClose={() => setSelected(null)}
            />
          )}

          {/* 지도의 표 보기: 색을 구분하기 어려워도 같은 정보를 읽을 수 있게 */}
          <section className="rounded-2xl bg-white p-4 shadow-card">
            <h2 className="mb-2 text-sm font-semibold text-slate-700">{t.heatmapRanking}</h2>
            {heatmap.loading && !heatmap.data ? (
              <p className="text-sm text-slate-500">{t.loading}</p>
            ) : (
              <table className="w-full text-sm">
                <thead className="sr-only">
                  <tr>
                    <th>{t.heatmapDistrict}</th>
                    <th>{item ? t.heatmapPrice : t.heatmapIndex}</th>
                    <th>{t.heatmapVsSeoul}</th>
                  </tr>
                </thead>
                <tbody>
                  {districts.map((d) => (
                    <tr
                      key={d.region}
                      onClick={() => setSelected(d.region)}
                      className={`cursor-pointer border-t border-slate-100 hover:bg-slate-50 ${selected === d.region ? "bg-brand-pale" : ""}`}
                    >
                      <td className="py-1.5">
                        {/* Keyboard access: the click bubbles to the row */}
                        <button className="flex items-center gap-2 text-left">
                          <span
                            className="h-3 w-3 shrink-0 rounded-sm"
                            style={{ background: binFor(d.diff_pct, mode).fill }}
                            aria-hidden
                          />
                          {dn(d.name)}
                        </button>
                      </td>
                      <td className="py-1.5 text-right font-semibold tabular-nums">
                        {d.price_avg != null ? formatKrw(d.price_avg) : d.index.toFixed(1)}
                      </td>
                      <td className="w-16 py-1.5 text-right text-xs tabular-nums text-slate-500">
                        {formatPct(d.diff_pct)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
