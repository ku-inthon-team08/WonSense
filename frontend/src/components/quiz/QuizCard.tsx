"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { quizFeedback, t, type QuizDirection, type QuizResult } from "@/lib/strings";

type Quiz = {
  item_id: number;
  name_ko: string;
  name_en: string;
  unit: string;
  question: string;
  answer_price: number;
  tolerance_correct: number;
  tolerance_close: number;
  tip: string;
  source: string;
  reference_date: string;
};

const won = (n: number) => `₩${n.toLocaleString("ko-KR")}`;

const RESULT_STYLE: Record<QuizResult, { box: string; word: string }> = {
  right: { box: "bg-green-100 text-green-900", word: t.quizRight },
  near: { box: "bg-amber-100 text-amber-900", word: t.quizNear },
  wrong: { box: "bg-rose-100 text-rose-900", word: t.quizWrong },
};

// Same rules as grade() in backend/app/services/quiz.py.
function grade(guess: number, quiz: Quiz): QuizResult {
  const error = Math.abs(guess - quiz.answer_price) / quiz.answer_price;
  if (error <= quiz.tolerance_correct) return "right";
  return error <= quiz.tolerance_close ? "near" : "wrong";
}

export function QuizCard() {
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [guess, setGuess] = useState("");
  const [result, setResult] = useState<QuizResult | null>(null);
  const [direction, setDirection] = useState<QuizDirection>("low");

  const load = useCallback(async (exclude?: number) => {
    setLoading(true);
    setError("");
    setGuess("");
    setResult(null);
    try {
      setQuiz(await api<Quiz>(`/api/quiz/random${exclude ? `?exclude=${exclude}` : ""}`));
    } catch {
      setError(t.quizError);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!quiz) return;
    const value = Number(guess);
    if (!guess || value <= 0) return setError(t.quizNeedNumber);
    setDirection(value > quiz.answer_price ? "high" : "low");
    setResult(grade(value, quiz));
  }

  return (
    <div className="flex min-h-64 flex-1 flex-col justify-between gap-4 rounded-xl bg-stone-100 p-4">
      <p className="text-lg font-medium text-slate-800">
        {loading ? t.quizLoading : quiz?.question}
      </p>

      {quiz && result !== null ? (
        <div className={`rounded-lg p-4 ${RESULT_STYLE[result].box}`}>
          <p className="text-xl font-bold">{RESULT_STYLE[result].word}</p>
          <p className="mt-1">{quizFeedback(result, direction, won(quiz.answer_price))}</p>
          {quiz.tip && <p className="mt-2 text-sm text-slate-600">{quiz.tip}</p>}
          <p className="mt-2 text-xs text-slate-500">
            {t.quizSource}: {quiz.source}, {quiz.reference_date}
          </p>
        </div>
      ) : (
        <form onSubmit={submit} className="flex gap-2">
          <input
            type="text"
            inputMode="numeric"
            placeholder="₩"
            value={guess}
            onChange={(e) => {
              setGuess(e.target.value.replace(/\D/g, "")); // numbers only
              setError("");
            }}
            disabled={!quiz || loading}
            className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2"
            aria-label="price guess in won"
          />
          <button
            disabled={!quiz || loading}
            className="rounded-lg bg-brand px-4 py-2 font-medium text-white disabled:opacity-50"
          >
            OK
          </button>
        </form>
      )}

      {error && <p className="text-sm text-rose-600">{error}</p>}

      {result !== null && (
        <button
          onClick={() => load(quiz?.item_id)}
          className="self-end rounded-lg border border-brand px-4 py-2 font-medium text-brand"
        >
          {t.quizNext} →
        </button>
      )}
    </div>
  );
}
