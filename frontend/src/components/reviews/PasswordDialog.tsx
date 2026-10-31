"use client";

import { useState } from "react";

import { t } from "@/lib/strings";

// Asks for the review's password and runs `onConfirm` with it. Errors (403 wrong / 429 locked)
// come back from the backend as readable messages and are shown inline.
export function PasswordDialog({
  message,
  danger = false,
  onConfirm,
  onClose,
}: {
  message: string;
  danger?: boolean;
  onConfirm: (password: string) => Promise<void>;
  onClose: () => void;
}) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await onConfirm(password);
    } catch (err) {
      setError((err as Error).message);
      setBusy(false);
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4"
      onClick={onClose}
    >
      <form
        onSubmit={submit}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-sm rounded-2xl bg-white p-5 shadow-xl"
      >
        <p className="text-sm text-slate-700">{message}</p>
        <input
          type="password"
          autoFocus
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          aria-label={t.review.password}
          autoComplete="current-password"
          className="mt-3 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-brand"
        />
        {error && <p className="mt-2 text-sm text-rose-600">{error}</p>}
        <div className="mt-4 flex justify-end gap-2">
          <button type="button" onClick={onClose} className="rounded-lg border border-slate-300 px-4 py-2 text-sm">
            {t.review.cancel}
          </button>
          <button
            type="submit"
            disabled={busy || !password}
            className={`rounded-lg px-4 py-2 text-sm font-medium text-white disabled:opacity-50 ${
              danger ? "bg-rose-600" : "bg-brand"
            }`}
          >
            {danger ? t.review.delete : t.review.confirm}
          </button>
        </div>
      </form>
    </div>
  );
}
