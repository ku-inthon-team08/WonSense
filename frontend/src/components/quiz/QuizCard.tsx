"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { t } from "@/lib/strings";

type Quiz = {
  item_id: number;
  name: string;
  unit: string;
  question: string;
  explanation: string;
  answer_price: number;
  price_min: number;
  price_max: number;
  tolerance: number;
  source: string;
  reference_date: string;
};

const won = (n: number) => `₩${n.toLocaleString("ko-KR")}`;

export function QuizCard() {
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [guess, setGuess] = useState("");
  const [result, setResult] = useState<boolean | null>(null);

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
    setResult(Math.abs(value - quiz.answer_price) / quiz.answer_price <= quiz.tolerance);
  }

  return (
    <div className="flex min-h-64 flex-1 flex-col justify-between gap-4 rounded-xl bg-stone-100 p-4">
      <p className="text-lg font-medium text-slate-800">
        {loading ? t.quizLoading : quiz?.question}
      </p>

      {quiz && result !== null ? (
        <div className={`rounded-lg p-4 ${result ? "bg-green-100 text-green-900" : "bg-rose-100 text-rose-900"}`}>
          <p className="text-xl font-bold">{result ? t.quizRight : t.quizWrong}</p>
          <p className="mt-1">
            {t.quizYourGuess}: {won(Number(guess))}
          </p>
          <p className="font-semibold">
            {t.quizAnswer}: {won(quiz.answer_price)}{" "}
            <span className="font-normal">
              ({won(quiz.price_min)} ~ {won(quiz.price_max)})
            </span>
          </p>
          <p className="mt-2 text-sm text-slate-700">{quiz.explanation}</p>
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
