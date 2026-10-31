"use client";

import { useState } from "react";
import { binFor, formatPct, formatWon, type HeatmapDistrict, type ScaleMode } from "@/lib/heatmap";
import { SEOUL_DISTRICTS, SEOUL_VIEWBOX } from "@/lib/seoulDistricts";
import { t } from "@/lib/strings";

type Props = {
  districts: HeatmapDistrict[];
  mode: ScaleMode;
  selected?: string | null;
  onSelect?: (region: string) => void;
  compact?: boolean; // 홈 미리보기: 라벨·툴팁·선택 없음
};

type Tip = { region: string; x: number; y: number };

export function SeoulMap({ districts, mode, selected, onSelect, compact = false }: Props) {
  const [tip, setTip] = useState<Tip | null>(null);
  const byRegion = new Map(districts.map((d) => [d.region, d]));
  const tipData = tip ? byRegion.get(tip.region) : undefined;
  const tipShape = tip ? SEOUL_DISTRICTS.find((s) => s.code === tip.region) : undefined;

  return (
    <div className="relative" onPointerLeave={() => setTip(null)}>
      <svg
        viewBox={`0 0 ${SEOUL_VIEWBOX.width} ${SEOUL_VIEWBOX.height}`}
        className="h-auto w-full"
        role={compact ? "img" : "group"}
        aria-label={t.heatmapMapLabel}
      >
        {SEOUL_DISTRICTS.map((shape) => {
          const d = byRegion.get(shape.code);
          const bin = d ? binFor(d.diff_pct, mode) : null;
          const isSelected = selected === shape.code;
          const interactive = !compact && d;
          return (
            <path
              key={shape.code}
              d={shape.d}
              fill={bin?.fill ?? "#e1e0d9"}
              stroke={isSelected ? "#0b0b0b" : "#ffffff"}
              strokeWidth={isSelected ? 3 : 1.5}
              strokeLinejoin="round"
              className={interactive ? "cursor-pointer outline-none transition-[filter] hover:brightness-95 focus-visible:brightness-90" : undefined}
              tabIndex={interactive ? 0 : undefined}
              role={interactive ? "button" : undefined}
              aria-pressed={interactive ? isSelected : undefined}
              aria-label={d ? `${shape.name} ${d.index} (${formatPct(d.diff_pct)})` : `${shape.name} ${t.heatmapNoData}`}
              onPointerMove={interactive ? (e) => {
                const box = e.currentTarget.ownerSVGElement!.getBoundingClientRect();
                setTip({ region: shape.code, x: e.clientX - box.left, y: e.clientY - box.top });
              } : undefined}
              onFocus={interactive ? (e) => {
                const box = e.currentTarget.ownerSVGElement!.getBoundingClientRect();
                const scale = box.width / SEOUL_VIEWBOX.width;
                setTip({ region: shape.code, x: shape.cx * scale, y: shape.cy * scale });
              } : undefined}
              onBlur={interactive ? () => setTip(null) : undefined}
              onClick={interactive ? () => onSelect?.(shape.code) : undefined}
              onKeyDown={interactive ? (e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onSelect?.(shape.code);
                }
              } : undefined}
            />
          );
        })}
        {/* 선택한 구의 테두리가 이웃 구에 가려지지 않도록 맨 위에 한 번 더 그린다 */}
        {selected && (
          <path
            d={SEOUL_DISTRICTS.find((s) => s.code === selected)?.d}
            fill="none"
            stroke="#0b0b0b"
            strokeWidth={3}
            strokeLinejoin="round"
            pointerEvents="none"
          />
        )}
        {!compact &&
          SEOUL_DISTRICTS.map((shape) => {
            const d = byRegion.get(shape.code);
            const ink = d ? binFor(d.diff_pct, mode).ink : "#52514e";
            return (
              <text
                key={shape.code}
                x={shape.cx}
                y={shape.cy}
                textAnchor="middle"
                dominantBaseline="central"
                // SVG 좌표 단위라서 지도가 작게 그려지는 휴대폰에서는 더 크게 둔다
                className="text-[24px] sm:text-[17px]"
                fontWeight={600}
                fill={ink}
                pointerEvents="none"
                aria-hidden
              >
                {shape.name}
              </text>
            );
          })}
      </svg>

      {tip && tipData && tipShape && (
        <div
          className="pointer-events-none absolute z-10 w-max max-w-56 -translate-x-1/2 -translate-y-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-lg"
          style={{ left: tip.x, top: tip.y - 12 }}
          role="status"
        >
          <div className="text-base font-bold tabular-nums">
            {tipData.index.toFixed(1)}{" "}
            <span className="text-sm font-medium text-slate-600">({formatPct(tipData.diff_pct)})</span>
          </div>
          {tipData.price_avg != null && (
            <div className="font-semibold tabular-nums">{formatWon(tipData.price_avg)}</div>
          )}
          <div className="text-slate-600">{tipShape.name}</div>
          {tipData.price_avg == null && (
            <div className="text-xs text-slate-500">{t.heatmapItemCount(tipData.item_count)}</div>
          )}
        </div>
      )}
    </div>
  );
}
