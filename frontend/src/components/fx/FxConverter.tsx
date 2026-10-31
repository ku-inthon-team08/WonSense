"use client";

import { useState } from "react";

import { formatKrw } from "@/lib/format";
import { fetchFx, type FxCurrency } from "@/lib/fx";
import { useLocale, useT } from "@/lib/i18n";
import { inputClass } from "@/lib/ui";
import { useApi } from "@/lib/useApi";

// inputClass is full width; the select sits beside the amount so it gets a fixed width instead.
const selectClass = inputClass.replace("w-full", "w-36 sm:w-56");

// Currencies quoted per 100 units are small enough that cents don't matter.
const digitsOf = (c: FxCurrency) => (c.unit === 100 ? 0 : 2);

/** Converter on the /fx page: an amount in a foreign currency → won, or won → that currency (swap button). */
export function FxConverter() {
  const t = useT();
  const locale = useLocale();
  const { data } = useApi("fx-all", (signal) => fetchFx(signal, true));
  const [code, setCode] = useState("USD");
  const [toKrw, setToKrw] = useState(true);
  const [amount, setAmount] = useState("100");

  const currencies = data?.currencies ?? [];
  const c = currencies.find((x) => x.code === code);
  const value = Number(amount.replace(/,/g, ""));
  const perUnit = c ? c.krw / c.unit : 0; // won per 1 unit of the currency
  const result = !c || !Number.isFinite(value) || value < 0 ? null : toKrw ? value * perUnit : value / perUnit;
  const names = new Intl.DisplayNames([locale], { type: "currency" });

  const select = (
    <select
      aria-label={t.fx.converter.currency}
      value={code}
      onChange={(e) => setCode(e.target.value)}
      className={`${selectClass} shrink-0 font-semibold`}
    >
      {currencies.map((x) => (
        <option key={x.code} value={x.code}>
          {x.code} · {names.of(x.code)}
        </option>
      ))}
    </select>
  );

  return (
    <section aria-label={t.fx.converter.title}>
      <h2 className="text-lg font-semibold text-slate-900">{t.fx.converter.title}</h2>

      <div className="mt-4 flex flex-col gap-3 md:flex-row md:items-center">
        <div className="flex flex-1 gap-2">
          {!toKrw && <span className="self-center text-lg font-semibold text-slate-500">₩</span>}
          <input
            aria-label={t.fx.converter.amount}
            inputMode="decimal"
            value={amount}
            onChange={(e) => setAmount(e.target.value.replace(/[^\d.,]/g, ""))}
            className={`${inputClass} min-w-0 flex-1 text-lg tabular-nums`}
          />
          {toKrw && select}
        </div>

        <button
          type="button"
          onClick={() => {
            setToKrw(!toKrw);
            if (result != null) setAmount(String(Math.round(result * 100) / 100));
          }}
          aria-label={t.fx.converter.swap}
          title={t.fx.converter.swap}
          className="grid h-10 w-10 shrink-0 place-items-center self-center rounded-full bg-brand-soft text-lg font-bold text-brand-ink transition-transform hover:rotate-180"
        >
          ⇄
        </button>

        <div className="flex flex-1 items-center gap-2 rounded-2xl bg-brand-pale px-4 py-2.5">
          <p className="min-w-0 flex-1 truncate text-2xl font-bold tabular-nums text-slate-900" aria-live="polite">
            {result == null || !c
              ? "–"
              : toKrw
                ? formatKrw(Math.round(result))
                : result.toLocaleString("en-US", { minimumFractionDigits: digitsOf(c), maximumFractionDigits: digitsOf(c) })}
          </p>
          {!toKrw && select}
        </div>
      </div>

      {c && (
        <p className="mt-3 text-[11px] leading-snug text-slate-500">
          {t.fx.converter.rate(t.fx.unit[c.code] ?? `${c.unit} ${c.code}`, formatKrw(Math.round(c.krw * 100) / 100))} ·{" "}
          {t.fx.converter.note}
        </p>
      )}
    </section>
  );
}
