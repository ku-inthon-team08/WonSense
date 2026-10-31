import { PageShell } from "@/components/PageShell";
import { QuizCard } from "@/components/quiz/QuizCard";
import { t } from "@/lib/strings";
import { card } from "@/lib/ui";

export default function QuizPage() {
  return (
    <PageShell title={t.quizTitle}>
      <section className={card}>
        <QuizCard />
      </section>
    </PageShell>
  );
}
