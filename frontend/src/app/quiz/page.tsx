"use client";

import Link from "next/link";
import { QuizCard } from "@/components/quiz/QuizCard";
import { useT } from "@/lib/i18n";

export default function QuizPage() {
  const t = useT();
  return (
    <main className="mx-auto w-full max-w-2xl flex-1 px-4 py-6">
      <Link href="/" className="text-sm text-brand">{t.home}</Link>
      <h1 className="mb-4 mt-2 text-2xl font-bold">{t.quizTitle}</h1>
      <QuizCard />
    </main>
  );
}
