"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";
import { useApi } from "@/lib/useApi";
import { ChoiceButtons } from "./ChoiceButtons";
import { GuessQuiz } from "./GuessQuiz";
import { ResultBox } from "./ResultBox";
import { quizName, quizQuestion } from "./text";
import type { Outcome, QuizData } from "./types";

function Chip({ children }: { children: React.ReactNode }) {
  return (
    <span className="self-start rounded-full bg-brand-pale px-3 py-1 text-base font-bold text-slate-900">
      {children}
    </span>
  );
}

export function QuizCard() {
  const t = useT();
  // Each round is one request; `exclude` keeps the same item from coming up twice in a row.
  const [round, setRound] = useState({ n: 0, exclude: "" });
  const [outcome, setOutcome] = useState<Outcome | null>(null);
  const { data: quiz, error } = useApi(`quiz:${round.n}`, (signal) => {
    const qs = round.exclude ? `?exclude=${encodeURIComponent(round.exclude)}` : "";
    return api<QuizData>(`/api/quiz/random${qs}`, { signal });
  });

  function next(exclude: string) {
    setOutcome(null);
    setRound({ n: round.n + 1, exclude });
  }

  return (
    <div className="flex flex-col gap-4 rounded-xl bg-stone-100 p-4">
      {!quiz ? (
        <p className="text-slate-600">{error ? t.quizError : t.quizLoading}</p>
      ) : (
        <>
          <span className="self-start rounded-md bg-brand px-2 py-0.5 text-xs font-semibold text-white">
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
