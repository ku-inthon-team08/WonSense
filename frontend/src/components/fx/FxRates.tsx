"use client";

import { useState } from "react";

import { FX_SYMBOL, fetchFx, formatFxKrw, type FxCurrency } from "@/lib/fx";
import { useT } from "@/lib/i18n";
import { useApi } from "@/lib/useApi";

// Exchange rates under the quiz: four stat tiles (value + day-over-day change + 14-day sparkline).
export function FxRates() {
  const t = useT();
  const { data, error } = useApi("fx", (signal) => fetchFx(signal));

  return (
    <section
      aria-label={t.fx.title}
      className="rounded-xl bg-gradient-to-br from-brand-pale/70 via-brand-pale/30 to-white p-4 ring-1 ring-brand/15"
    >
      <header className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
        <h3 className="flex items-center gap-2 whitespace-nowrap text-sm font-semibold text-slate-800">
          <span aria-hidden className="grid h-6 w-6 place-items-center rounded-full bg-brand text-xs text-white">
            ₩
          </span>
          {t.fx.title}
        </h3>
        {data && (
          <span className="whitespace-nowrap text-xs text-slate-500">
            {t.fx.asOf(data.date)} · {t.fx.vsPrev}
          </span>
        )}
      </header>

      {error ? (
        <p className="mt-3 text-sm text-slate-500">{t.fx.error}</p>
      ) : (
        <ul className="mt-3 grid grid-cols-2 gap-2.5">
          {data
            ? data.currencies.map((c) => (
                <li key={c.code}>
                  <FxTile c={c} />
                </li>
              ))
            : [0, 1, 2, 3].map((i) => (
                <li key={i} aria-hidden className="h-[118px] animate-pulse rounded-lg bg-white/70" />
              ))}
        </ul>
      )}

      {data && (
        <p className="mt-3 text-[11px] leading-snug text-slate-500">
          {t.fx.note} · {t.quizSource}: {t.sourceName(data.source)}
        </p>
      )}
    </section>
  );
}

function FxTile({ c }: { c: FxCurrency }) {
  const t = useT();
  const [hover, setHover] = useState<number | null>(null);
  const point = hover != null ? c.history[hover] : null;
  const unit = t.fx.unit[c.code] ?? `${c.unit} ${c.code}`;

  return (
    <div className="rounded-lg bg-white p-3 shadow-card transition-shadow hover:ring-1 hover:ring-brand/40">
      <div className="flex items-center gap-2">
        <span
          aria-hidden
          className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-brand-pale text-sm font-bold text-brand"
        >
          {FX_SYMBOL[c.code]}
        </span>
        <div className="min-w-0 leading-tight">
          <p className="text-xs font-semibold tracking-wide text-slate-800">{c.code}</p>
          <p className="truncate text-[11px] text-slate-500">{unit}</p>
        </div>
      </div>

      <p className="mt-2 text-xl font-semibold tabular-nums text-slate-900">
        {formatFxKrw(point ? point.krw : c.krw)}
      </p>

      {/* While hovering the sparkline this line shows the hovered day instead of the change */}
      <p className="h-4 truncate text-xs tabular-nums text-slate-500">
        {point ? point.date : <Change pct={c.change_pct} />}
      </p>

      <Sparkline
        points={c.history.map((p) => p.krw)}
        active={hover}
        onActive={setHover}
        label={`${c.code} ${t.fx.trend(c.history.length)}`}
      />
    </div>
  );
}

function Change({ pct }: { pct: number | null }) {
  if (pct == null) return null;
  // A rising rate is neither good nor bad here, so the change stays in neutral ink.
  const arrow = pct > 0 ? "▲" : pct < 0 ? "▼" : "–";
  const sign = pct > 0 ? "+" : "";
  return (
    <span className="font-medium text-slate-700">
      {arrow} {sign}
      {pct.toFixed(2)}%
    </span>
  );
}

const W = 100;
const H = 28;
const PAD = 3;

function Sparkline({
  points,
  active,
  onActive,
  label,
}: {
  points: number[];
  active: number | null;
  onActive: (i: number | null) => void;
  label: string;
}) {
  if (points.length < 2) return <div className="mt-2 h-7" />;
  const min = Math.min(...points);
  const max = Math.max(...points);
  const span = max - min || 1;
  const x = (i: number) => (i / (points.length - 1)) * W;
  const y = (v: number) => PAD + (1 - (v - min) / span) * (H - PAD * 2);
  const line = points.map((v, i) => `${x(i).toFixed(2)},${y(v).toFixed(2)}`).join(" ");
  const area = `0,${H} ${line} ${W},${H}`;
  const last = points.length - 1;
  const dot = active ?? last;

  function pick(clientX: number, el: HTMLElement) {
    const box = el.getBoundingClientRect();
    const i = Math.round(((clientX - box.left) / box.width) * last);
    onActive(Math.max(0, Math.min(last, i)));
  }

  return (
    <div
      role="img"
      aria-label={label}
      tabIndex={0}
      className="relative mt-2 h-7 cursor-crosshair rounded outline-none focus-visible:ring-2 focus-visible:ring-brand/50"
      onPointerMove={(e) => pick(e.clientX, e.currentTarget)}
      onPointerLeave={() => onActive(null)}
      onBlur={() => onActive(null)}
      onKeyDown={(e) => {
        if (e.key === "ArrowLeft") onActive(Math.max(0, (active ?? last) - 1));
        else if (e.key === "ArrowRight") onActive(Math.min(last, (active ?? last) + 1));
        else if (e.key === "Escape") onActive(null);
      }}
    >
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="h-full w-full overflow-visible" aria-hidden>
        <polygon points={area} className="fill-brand-pale/60" />
        <polyline
          points={line}
          fill="none"
          strokeWidth={2}
          strokeLinejoin="round"
          strokeLinecap="round"
          vectorEffect="non-scaling-stroke"
          className="stroke-stone-300"
        />
        {active != null && (
          <line
            x1={x(active)}
            x2={x(active)}
            y1={0}
            y2={H}
            strokeWidth={1}
            vectorEffect="non-scaling-stroke"
            className="stroke-slate-400"
          />
        )}
      </svg>
      {/* Drawn in HTML so the dot stays round while the SVG stretches to the tile width */}
      <span
        aria-hidden
        className="pointer-events-none absolute h-2.5 w-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-brand ring-2 ring-white"
        style={{ left: `${(x(dot) / W) * 100}%`, top: `${(y(points[dot]) / H) * 100}%` }}
      />
    </div>
  );
}
