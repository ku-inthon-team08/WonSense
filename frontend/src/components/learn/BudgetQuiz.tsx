"use client";

import { useState } from "react";

import { formatKrw } from "@/lib/format";
import { fetchFx, formatFromKrw } from "@/lib/fx";
import { useT } from "@/lib/i18n";
import { cardName, dealBudgetQuestion, familiarBuys, type PriceCard } from "@/lib/learn";
import { useApi } from "@/lib/useApi";

const OPTION_STYLE = {
  open: "border-brand bg-white text-slate-800 hover:bg-brand-pale active:scale-95",
  right: "border-green-600 bg-green-100 text-green-900",
  wrong: "border-rose-500 bg-rose-100 text-rose-900",
  other: "border-slate-200 bg-white text-slate-500",
};

// "Which one can you buy with this?" Exactly one option fits; answering shows what the money really gets you.
export function BudgetQuiz({ cards }: { cards: PriceCard[] }) {
  const t = useT();
  const [question, setQuestion] = useState(() => dealBudgetQuestion(cards));
  const [picked, setPicked] = useState<PriceCard | null>(null);
  const [code, setCode] = useState("USD");
  const { data: fx } = useApi("fx", (signal) => fetchFx(signal));

  if (!question) return <p className="py-6 text-center text-slate-500">{t.learn.error}</p>;

  const { budget, answer, options } = question;
  const currency = fx?.currencies.find((c) => c.code === code);
  const right = picked?.key === answer.key;

  function styleOf(card: PriceCard) {
    if (!picked) return OPTION_STYLE.open;
    if (card.key === answer.key) return OPTION_STYLE.right;
    return card.key === picked.key ? OPTION_STYLE.wrong : OPTION_STYLE.other;
  }

  function next() {
    setQuestion(dealBudgetQuestion(cards, budget));
    setPicked(null);
  }

  return (
    <div className="flex flex-1 flex-col gap-4">
      <div className="flex flex-col gap-3 rounded-2xl bg-brand-pale p-4 md:p-5">
        <div className="flex flex-wrap items-baseline justify-between gap-x-3">
          <p className="text-4xl font-bold tabular-nums text-slate-900">{formatKrw(budget)}</p>
          {currency && <span className="tabular-nums text-slate-600">≈ {formatFromKrw(budget, currency)}</span>}
        </div>

        {fx && (
          <div role="group" aria-label={t.learn.currencyLabel} className="flex flex-wrap gap-1.5">
            {fx.currencies.map((c) => (
              <button
                key={c.code}
                type="button"
                aria-pressed={c.code === code}
                onClick={() => setCode(c.code)}
                className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                  c.code === code ? "bg-brand text-slate-900" : "bg-white text-slate-600 ring-1 ring-slate-200"
                }`}
              >
                {c.code}
              </button>
            ))}
          </div>
        )}

        <p className="text-lg font-medium text-slate-800">{t.learn.budgetQuestion}</p>

        <div className="grid grid-cols-2 gap-2">
          {options.map((card) => (
            <button
              key={card.key}
              type="button"
              disabled={picked !== null}
              onClick={() => setPicked(card)}
              className={`rounded-xl border-2 px-3 py-3 text-base font-semibold transition-colors ${styleOf(card)}`}
            >
              {cardName(t, card)}
              {picked && <span className="mt-0.5 block text-sm font-medium tabular-nums">{formatKrw(card.price)}</span>}
            </button>
          ))}
        </div>
      </div>

      {picked && (
        <>
          <div className={`quiz-pop rounded-lg p-3 ${right ? "bg-green-100 text-green-900" : "bg-rose-100 text-rose-900"}`} role="status">
            <p className="font-bold">{right ? t.quizVerdict.right : t.quizVerdict.wrong}</p>
            <p className="mt-1 text-sm">
              {cardName(t, picked)}: {right ? t.learn.budgetLeft(picked.price, budget - picked.price) : t.learn.budgetShort(picked.price, picked.price - budget)}
            </p>
          </div>

          <div>
            <h3 className="mb-2 text-sm font-semibold text-slate-700">{t.learn.buys}</h3>
            <ul className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              {familiarBuys(cards, budget).map(({ card, count }) => (
                <li key={card.key} className={`rounded-xl bg-brand-pale p-3 ${count === 0 ? "opacity-50" : ""}`}>
                  <p className="text-2xl font-bold tabular-nums text-brand-ink">×{count}</p>
                  <p className="mt-0.5 line-clamp-2 text-xs font-medium text-slate-800">{cardName(t, card)}</p>
                  <p className="text-xs tabular-nums text-slate-500">{formatKrw(card.price)}</p>
                </li>
              ))}
            </ul>
          </div>

          <button
            type="button"
            onClick={next}
            className="self-end rounded-lg border border-brand px-4 py-2 font-medium text-brand-ink"
          >
            {t.quizNext} →
          </button>
        </>
      )}
    </div>
  );
}
