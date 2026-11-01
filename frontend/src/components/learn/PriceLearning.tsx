"use client";

import type { ReactNode } from "react";

import { LadderIcon, WonIcon } from "@/components/icons/SectionIcons";
import { useT } from "@/lib/i18n";
import { RUNGS, fetchPriceCards } from "@/lib/learn";
import { card } from "@/lib/ui";
import { useApi } from "@/lib/useApi";

import { BudgetQuiz } from "./BudgetQuiz";
import { PriceLadder } from "./PriceLadder";
import { SkeletonLines } from "@/components/Skeleton";

function Title({ icon, children }: { icon: ReactNode; children: ReactNode }) {
  return (
    <h2 className="mb-4 flex items-center gap-2.5 text-lg font-semibold text-slate-900">
      <span aria-hidden className="grid h-8 w-8 place-items-center rounded-full bg-brand-soft text-brand-ink">
        {icon}
      </span>
      {children}
    </h2>
  );
}

// Under the quiz: two more ways to get a feel for Seoul prices, both showing the real prices after each answer.
export function PriceLearning() {
  const t = useT();
  const { data, error } = useApi("price-cards", (signal) => fetchPriceCards(signal));
  const ready = data && data.cards.length >= RUNGS;
  const status =
    !ready &&
    (error || data ? (
      <p className="py-6 text-center text-slate-500">{t.learn.error}</p>
    ) : (
      <SkeletonLines label={t.loading} lines={4} className="py-4" />
    ));

  return (
    <div className="mt-6 grid gap-6 lg:grid-cols-2">
      <section className={card}>
        <Title icon={<WonIcon className="h-4 w-4" />}>{t.learn.budgetTitle}</Title>
        {ready ? <BudgetQuiz cards={data.cards} /> : status}
        <p className="mt-4 text-xs text-slate-500">
          {t.learn.note}
          {data?.reference_date && ` · ${t.learn.asOf(data.reference_date)}`}
        </p>
      </section>

      <section className={card}>
        <Title icon={<LadderIcon className="h-4 w-4" />}>{t.learn.ladderTitle}</Title>
        {ready ? <PriceLadder cards={data.cards} /> : status}
      </section>
    </div>
  );
}
