"use client";

import Link from "next/link";
import { useState } from "react";

import { FX_SYMBOL, fetchFx, formatFxKrw, type FxCurrency } from "@/lib/fx";
import { MAX_PICKS, toggleFxPick, useFxPicks } from "@/lib/fxPicks";
import { ArrowRightIcon, ExchangeIcon } from "@/components/icons/SectionIcons";
import { useT } from "@/lib/i18n";
import { useApi } from "@/lib/useApi";

// Exchange rates: stat tiles (value + day-over-day change + 14-day sparkline).
// Home passes `href` so the title links to /fx and shows the (up to four) currencies the visitor picked;
// the /fx page passes `all` for every currency and `hideTitle` because PageShell already shows it.
export function FxRates({ href, hideTitle = false, all = false }: { href?: string; hideTitle?: boolean; all?: boolean }) {
  const t = useT();
  const { data, error } = useApi("fx-all", (signal) => fetchFx(signal, true));
  const picks = useFxPicks();
  const [editing, setEditing] = useState(false);
  const shown = all
    ? data?.currencies
    : data && picks.flatMap((code) => data.currencies.filter((c) => c.code === code));

  return (
    <section aria-label={t.fx.title}>
      <header className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
        {!hideTitle && (
          <h2 className="whitespace-nowrap text-lg font-semibold text-slate-900">
            {href ? (
              <Link href={href} className="group flex items-center gap-2.5">
                <FxTitle title={t.fx.title} />
                <ArrowRightIcon className="h-4 w-4 text-brand-ink transition-transform group-hover:translate-x-1" />
              </Link>
            ) : (
              <span className="flex items-center gap-2.5">
                <FxTitle title={t.fx.title} />
              </span>
            )}
          </h2>
        )}
        <div className="flex items-center gap-2">
          {data && (
            <span className="whitespace-nowrap text-xs text-slate-500">
              {t.fx.asOf(data.date)} · {t.fx.vsPrev}
            </span>
          )}
          {!all && data && (
            <button
              type="button"
              aria-expanded={editing}
              onClick={() => setEditing(!editing)}
              className="whitespace-nowrap rounded-full bg-brand-soft px-2.5 py-0.5 text-xs font-semibold text-brand-ink hover:brightness-95"
            >
              {editing ? t.fx.pickDone : t.fx.pickEdit}
            </button>
          )}
        </div>
      </header>

      {editing && data && (
        <div className="mt-3 rounded-2xl bg-brand-pale p-3">
          <p className="mb-2 text-xs text-slate-600">{t.fx.pickHint(MAX_PICKS)}</p>
          <div role="group" aria-label={t.fx.pickEdit} className="flex flex-wrap gap-1.5">
            {data.currencies.map((c) => {
              const on = picks.includes(c.code);
              return (
                <button
                  key={c.code}
                  type="button"
                  aria-pressed={on}
                  onClick={() => toggleFxPick(c.code)}
                  className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                    on ? "bg-brand text-slate-900" : "bg-white text-slate-600 ring-1 ring-slate-200"
                  }`}
                >
                  {c.code}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {error ? (
        <p className="mt-3 text-sm text-slate-500">{t.fx.error}</p>
      ) : (
        <ul className={`mt-4 grid grid-cols-2 gap-3 ${all ? "sm:grid-cols-3 lg:grid-cols-4" : ""}`}>
          {shown
            ? shown.map((c) => (
                <li key={c.code}>
                  <FxTile c={c} />
                </li>
              ))
            : Array.from({ length: all ? 12 : 4 }, (_, i) => (
                <li key={i} aria-hidden className="h-[118px] animate-pulse rounded-2xl bg-brand-pale" />
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

function FxTitle({ title }: { title: string }) {
  return (
    <>
      <span aria-hidden className="grid h-8 w-8 place-items-center rounded-full bg-brand-soft text-brand-ink">
        <ExchangeIcon className="h-4 w-4" />
      </span>
      {title}
    </>
  );
}

function FxTile({ c }: { c: FxCurrency }) {
  const t = useT();
  const [hover, setHover] = useState<number | null>(null);
  const point = hover != null ? c.history[hover] : null;
  const unit = t.fx.unit[c.code] ?? `${c.unit} ${c.code}`;

  return (
    <div className="rounded-2xl bg-white p-3.5 ring-1 ring-slate-100 transition-shadow hover:ring-brand/40">
      <div className="flex items-center gap-2">
        <span
          aria-hidden
          className={`grid h-7 w-7 shrink-0 place-items-center rounded-full bg-brand-soft font-bold text-brand-ink ${
            (FX_SYMBOL[c.code] ?? c.code).length > 2 ? "text-[9px]" : "text-sm"
          }`}
        >
          {FX_SYMBOL[c.code] ?? c.code}
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
        <polygon points={area} className="fill-brand-soft/60" />
        <polyline
          points={line}
          fill="none"
          strokeWidth={2}
          strokeLinejoin="round"
          strokeLinecap="round"
          vectorEffect="non-scaling-stroke"
          className="stroke-brand"
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
