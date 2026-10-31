"use client";

import Image from "next/image";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";
import { ChoiceButtons } from "./ChoiceButtons";
import { GuessQuiz } from "./GuessQuiz";
import { ResultBox } from "./ResultBox";
import { quizName, quizQuestion } from "./text";
import type { Outcome, QuizData } from "./types";

function Chip({ children }: { children: React.ReactNode }) {
  return (
    <span className="self-start rounded-full bg-brand-soft px-3 py-1 text-base font-bold text-slate-900">
      {children}
    </span>
  );
}

// mascot: 문제 영역 오른쪽에 전구 든 호랑이를 둔다 (홈 카드용, 넓은 화면에서만)
export function QuizCard({ mascot = false }: { mascot?: boolean }) {
  const t = useT();
  const [quiz, setQuiz] = useState<QuizData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [outcome, setOutcome] = useState<Outcome | null>(null);

  const fetchQuiz = useCallback((exclude?: string) => {
    const qs = exclude ? `?exclude=${encodeURIComponent(exclude)}` : "";
    return api<QuizData>(`/api/quiz/random${qs}`)
      .then(setQuiz)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchQuiz();
  }, [fetchQuiz]);

  function next(exclude: string) {
    setLoading(true);
    setError(false);
    setOutcome(null);
    fetchQuiz(exclude);
  }

  return (
    <div
      className={`relative flex flex-1 flex-col gap-4 overflow-hidden rounded-2xl bg-brand-pale p-4 md:p-5 ${mascot ? "lg:min-h-40" : ""}`}
    >
      {mascot && (
        <Image
          src="/mascot/horangi-3d-hold-lightbulb.webp"
          alt=""
          width={734}
          height={640}
          className="pointer-events-none absolute -right-2 top-3 hidden h-28 w-auto lg:block"
        />
      )}
      {loading || !quiz ? (
        <p className="text-slate-600">{error ? t.quizError : t.quizLoading}</p>
      ) : (
        <>
          {/* 문제 부분: 호랑이 그림과 겹치지 않게 넓은 화면에서 오른쪽을 비운다 */}
          <div className={`flex flex-col gap-4 ${mascot ? "lg:pr-32" : ""}`}>
            <span className="self-start rounded-full bg-brand px-2.5 py-0.5 text-xs font-semibold text-slate-900">
              {t.quizTypes[quiz.type]}
            </span>

            {quiz.type === "guess" && <Chip>{quizName(t, quiz)}</Chip>}
            {quiz.type === "menu" && (
              <div className="flex items-baseline gap-3">
                <Chip>{quizName(t, quiz)}</Chip>
                <span className="text-2xl font-bold text-slate-900">{t.quizShownPrice(quiz.shown_price)}</span>
              </div>
            )}
            <p className="text-lg font-medium text-slate-800">{quizQuestion(t, quiz)}</p>
          </div>

          {outcome ? (
            <ResultBox outcome={outcome} quiz={quiz} />
          ) : quiz.type === "guess" ? (
            <GuessQuiz key={quiz.key} quiz={quiz} onAnswer={setOutcome} />
          ) : quiz.type === "higher_lower" ? (
            <ChoiceButtons
              options={[
                { value: "higher", label: t.quizHigher },
                { value: "lower", label: t.quizLower },
              ]}
              onPick={(v) => setOutcome({ result: v === quiz.answer ? "right" : "wrong" })}
            />
          ) : (
            <ChoiceButtons
              options={[
                { value: "normal", label: t.quizNormal },
                { value: "above", label: t.quizAbove },
              ]}
              onPick={(v) => setOutcome({ result: v === quiz.answer ? "right" : "wrong" })}
            />
          )}

          {outcome && (
            <button
              onClick={() => next(quiz.key)}
              className="self-end rounded-lg border border-brand px-4 py-2 font-medium text-brand-ink"
            >
              {t.quizNext} →
            </button>
          )}
        </>
      )}
    </div>
  );
}
