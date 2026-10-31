"use client";

import { useState } from "react";
import { useT } from "@/lib/i18n";
import type { GuessQuizData, Outcome } from "./types";

// backend/app/services/quiz.py의 grade()와 같은 규칙
function grade(guess: number, q: GuessQuizData): Outcome["result"] {
  const error = Math.abs(guess - q.answer_price) / q.answer_price;
  if (error <= q.tolerance_correct) return "right";
  return error <= q.tolerance_close ? "near" : "wrong";
}

export function GuessQuiz({ quiz, onAnswer }: { quiz: GuessQuizData; onAnswer: (o: Outcome) => void }) {
  const t = useT();
  const [digits, setDigits] = useState("");
  const [error, setError] = useState("");

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const value = Number(digits);
    if (!digits || value <= 0) return setError(t.quizNeedNumber);
    const result = grade(value, quiz);
    onAnswer({ result, direction: value > quiz.answer_price ? "high" : "low" });
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-2">
      <div className="flex gap-2">
        <label className="flex w-full items-center rounded-lg border border-slate-300 bg-white px-3 focus-within:border-brand">
          <input
            type="text"
            inputMode="numeric"
            placeholder={t.quizGuessPlaceholder}
            value={digits ? Number(digits).toLocaleString("ko-KR") : ""}
            onChange={(e) => {
              setDigits(e.target.value.replace(/\D/g, "").slice(0, 9)); // 숫자만
              setError("");
            }}
            className="w-full bg-transparent py-2 text-right text-lg outline-none"
            aria-label={t.quizPriceLabel}
            autoFocus
          />
          <span className="ml-1 text-slate-500">{t.quizWon}</span>
        </label>
        <button className="rounded-lg bg-brand px-5 py-2 font-medium text-slate-900">OK</button>
      </div>
      {error && <p className="text-sm text-rose-600">{error}</p>}
    </form>
  );
}
