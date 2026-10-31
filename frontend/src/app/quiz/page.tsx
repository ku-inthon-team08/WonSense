"use client";

import { PageShell } from "@/components/PageShell";
import { PriceLearning } from "@/components/learn/PriceLearning";
import { QuizCard } from "@/components/quiz/QuizCard";
import { useT } from "@/lib/i18n";
import { card } from "@/lib/ui";

export default function QuizPage() {
  const t = useT();
  return (
    <PageShell title={t.quizTitle}>
      <section className={card}>
        <QuizCard />
      </section>
      <PriceLearning />
    </PageShell>
  );
}
