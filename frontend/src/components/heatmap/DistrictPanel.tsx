"use client";

import { useEffect, useRef } from "react";
import { formatKrw } from "@/lib/format";
import { formatPct, getDistrictDetail, type DistrictItem, type HeatmapDistrict, type HeatmapItem } from "@/lib/heatmap";
import { useApi } from "@/lib/useApi";
import { useDistrictName, useT } from "@/lib/i18n";
import { SkeletonLines } from "@/components/Skeleton";

type Props = {
  district: HeatmapDistrict;
  item: HeatmapItem | null; // 품목을 골랐으면 그 품목만 비교
  onClose: () => void;
};

export function DistrictPanel({ district, item, onClose }: Props) {
  const t = useT();
  const dn = useDistrictName();
  const detail = useApi(item ? null : `district:${district.region}`, (signal) =>
    getDistrictDetail(district.region, { signal }),
  );
  const items = detail.data?.items ?? [];
  const pricier = items.filter((i) => i.diff_pct > 0).slice(0, 5);
  const cheaper = items.filter((i) => i.diff_pct < 0).slice(-5).reverse();

  // 좁은 화면에서는 패널이 지도 아래에 열리므로, 구를 고르면 패널이 보이게 스크롤한다
  const ref = useRef<HTMLElement>(null);
  useEffect(() => {
    ref.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, []);

  return (
    <section ref={ref} className="rounded-2xl bg-white p-4 shadow-card" aria-live="polite">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h2 className="text-lg font-bold">{dn(district.name)}</h2>
          {item ? (
            <p className="text-sm text-slate-600">
              {t.heatmapVsSeoul}{" "}
              <span className="font-semibold tabular-nums text-slate-900">{formatPct(district.diff_pct)}</span>
            </p>
          ) : (
            <p className="text-sm text-slate-600">
              {t.heatmapIndex}{" "}
              <span className="font-semibold tabular-nums text-slate-900">{district.index.toFixed(1)}</span>{" "}
              ({t.heatmapVsSeoul} {formatPct(district.diff_pct)})
            </p>
          )}
        </div>
        <button
          onClick={onClose}
          className="rounded-full px-2 text-xl leading-none text-slate-500 hover:bg-slate-100"
          aria-label={t.close}
        >
          ×
        </button>
      </div>

      {item ? (
        district.price_avg != null && (
          <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
            <div className="rounded-lg bg-slate-50 p-3">
              <dt className="text-slate-500">{dn(district.name)}</dt>
              <dd className="text-lg font-bold tabular-nums">{formatKrw(district.price_avg)}</dd>
            </div>
            <div className="rounded-lg bg-slate-50 p-3">
              <dt className="text-slate-500">{t.heatmapSeoulAvg}</dt>
              <dd className="text-lg font-bold tabular-nums">{formatKrw(item.seoul_avg)}</dd>
            </div>
          </dl>
        )
      ) : detail.loading ? (
        <SkeletonLines label={t.loading} lines={4} className="mt-3" />
      ) : detail.error ? (
        <p className="mt-3 text-sm text-red-700">{t.heatmapError}</p>
      ) : (
        <div className="mt-3 grid gap-4 sm:grid-cols-2">
          <ItemList title={t.heatmapPricierItems} items={pricier} />
          <ItemList title={t.heatmapCheaperItems} items={cheaper} />
        </div>
      )}
    </section>
  );
}

function ItemList({ title, items }: { title: string; items: DistrictItem[] }) {
  const t = useT();
  return (
    <div>
      <h3 className="mb-1 text-sm font-semibold text-slate-700">{title}</h3>
      {items.length === 0 ? (
        <p className="text-sm text-slate-500">{t.heatmapNoData}</p>
      ) : (
        <ul className="divide-y divide-slate-100 text-sm">
          {items.map((i) => (
            <li key={i.item_id} className="flex items-baseline justify-between gap-2 py-1.5">
              <span className="min-w-0 truncate" title={i.name}>{i.name}</span>
              <span className="shrink-0 text-right tabular-nums">
                <span className="font-semibold">{formatKrw(i.price_avg)}</span>{" "}
                <span className="text-xs text-slate-500">{formatPct(i.diff_pct)}</span>
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
