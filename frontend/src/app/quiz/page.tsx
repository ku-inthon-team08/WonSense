"use client";

import { PageShell } from "@/components/PageShell";
import { FxRates } from "@/components/fx/FxRates";
import { QuizCard } from "@/components/quiz/QuizCard";
import { useT } from "@/lib/i18n";
import { card } from "@/lib/ui";

export default function QuizPage() {
  const t = useT();
  return (
    <PageShell title={t.quizTitle}>
      <section className={card}>
        <QuizCard />
        <div className="mt-5">
          <FxRates />
        </div>
      </section>
    </PageShell>
  );
}
