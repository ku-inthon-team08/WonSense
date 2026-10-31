import { t } from "@/lib/strings";
import type { Outcome } from "./types";

const STYLE: Record<Outcome["result"], string> = {
  right: "bg-green-100 text-green-900",
  near: "bg-amber-100 text-amber-900",
  wrong: "bg-rose-100 text-rose-900",
};

export function ResultBox({ outcome, source }: { outcome: Outcome; source: string }) {
  return (
    <div className={`quiz-pop rounded-lg p-4 ${STYLE[outcome.result]}`} role="status">
      <p className="text-xl font-bold">{t.quizVerdict[outcome.result]}</p>
      <p className="mt-1">{outcome.feedback}</p>
      {outcome.tip && <p className="mt-2 text-sm text-slate-600">💡 {outcome.tip}</p>}
      <p className="mt-2 text-xs text-slate-500">
        {t.quizSource}: {source}
      </p>
    </div>
  );
}
