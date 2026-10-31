"use client";

import { t } from "@/lib/strings";

// Placeholder for F2. Will fetch GET /api/quiz/today once the backend is in.
export function QuizCard() {
  return (
    <div className="flex min-h-64 flex-col justify-between rounded-xl bg-indigo-50 p-4">
      <p className="text-slate-600">{t.quizLoading}</p>
      <div className="mt-4 flex gap-2">
        <input
          type="number"
          inputMode="numeric"
          placeholder="₩"
          disabled
          className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2"
        />
        <button disabled className="rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white opacity-50">
          OK
        </button>
      </div>
    </div>
  );
}
