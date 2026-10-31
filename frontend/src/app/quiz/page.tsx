import Link from "next/link";
import { QuizCard } from "@/components/quiz/QuizCard";
import { t } from "@/lib/strings";

export default function QuizPage() {
  return (
    <main className="mx-auto w-full max-w-2xl flex-1 px-4 py-6">
      <Link href="/" className="text-sm text-brand">{t.home}</Link>
      <h1 className="mb-4 mt-2 text-2xl font-bold">{t.quizTitle}</h1>
      <QuizCard />
    </main>
  );
}
