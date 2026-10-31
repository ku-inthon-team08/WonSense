"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";
import type { Strings } from "@/lib/strings";
import { ChoiceButtons } from "./ChoiceButtons";
import { GuessQuiz } from "./GuessQuiz";
import { ResultBox } from "./ResultBox";
import type { Outcome, QuizData } from "./types";

function Chip({ children }: { children: React.ReactNode }) {
  return (
    <span className="self-start rounded-full bg-brand-pale px-3 py-1 text-base font-bold text-slate-900">
      {children}
    </span>
  );
}

// The server writes questions in Korean; in English we rebuild the ones whose parts we have.
function questionFor(t: Strings, quiz: QuizData): string {
  if (quiz.type === "higher_lower" && t.quizHigherLowerQuestion)
    return t.quizHigherLowerQuestion(quiz.target.name, quiz.base.name, quiz.base.price);
  if (quiz.type === "menu" && t.quizMenuQuestion) return t.quizMenuQuestion(quiz.menu_name, quiz.shown_price);
  return quiz.question;
}

export function QuizCard() {
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
    <div className="flex flex-col gap-4 rounded-xl bg-stone-100 p-4">
      {loading || !quiz ? (
        <p className="text-slate-600">{error ? t.quizError : t.quizLoading}</p>
      ) : (
        <>
          <span className="self-start rounded-md bg-brand px-2 py-0.5 text-xs font-semibold text-white">
            {t.quizTypes[quiz.type]}
          </span>

          {quiz.type === "guess" && <Chip>{quiz.quiz_name}</Chip>}
          {quiz.type === "menu" && (
            <div className="flex items-baseline gap-3">
              <Chip>{quiz.menu_name}</Chip>
              <span className="text-2xl font-bold text-slate-900">{t.quizShownPrice(quiz.shown_price)}</span>
            </div>
          )}
          <p className="text-lg font-medium text-slate-800">{questionFor(t, quiz)}</p>

          {outcome ? (
            <ResultBox outcome={outcome} source={quiz.source} />
          ) : quiz.type === "guess" ? (
            <GuessQuiz key={quiz.key} quiz={quiz} onAnswer={setOutcome} />
          ) : quiz.type === "higher_lower" ? (
            <ChoiceButtons
              options={[
                { value: "higher", label: t.quizHigher },
                { value: "lower", label: t.quizLower },
              ]}
              onPick={(v) =>
                setOutcome({
                  result: v === quiz.answer ? "right" : "wrong",
                  feedback: t.quizFeedback.higherLower(quiz.target.name, quiz.target.price),
                })
              }
            />
          ) : (
            <ChoiceButtons
              options={[
                { value: "normal", label: t.quizNormal },
                { value: "above", label: t.quizAbove },
              ]}
              onPick={(v) =>
                setOutcome({
                  result: v === quiz.answer ? "right" : "wrong",
                  feedback: t.quizFeedback.menu(quiz.answer, quiz.normal_low, quiz.normal_high),
                })
              }
            />
          )}

          {outcome && (
            <button
              onClick={() => next(quiz.key)}
              className="self-end rounded-lg border border-brand px-4 py-2 font-medium text-brand"
            >
              {t.quizNext} →
            </button>
          )}
        </>
      )}
    </div>
  );
}
