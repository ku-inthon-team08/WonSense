"use client";

import { useRouter } from "next/navigation";
import { useState, type ReactNode } from "react";

import {
  LIMITS,
  PRICE_FEELINGS,
  createReview,
  passwordError,
  updateReview,
  type PriceFeeling,
  type Review,
  type ReviewFields,
  type StoreRef,
} from "@/lib/reviews";
import { useT } from "@/lib/i18n";
import { inputClass } from "@/lib/ui";

import { StorePicker, type StoreChoice } from "./StorePicker";

function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <label className="flex flex-col gap-1 text-sm font-medium text-slate-700">
      {label}
      {children}
      {hint && <span className="text-xs font-normal text-slate-500">{hint}</span>}
    </label>
  );
}

type Props =
  | { mode: "create" }
  // Edit: the password was already checked by POST /verify and is re-sent with the PATCH.
  | { mode: "edit"; review: Review; password: string; onSaved: (r: Review) => void; onCancel: () => void };

export function ReviewForm(props: Props) {
  const t = useT();
  const router = useRouter();
  const initial = props.mode === "edit" ? props.review : null;

  const [store, setStore] = useState<StoreChoice>(initial?.store ? { kind: "existing", store: initial.store } : null);
  const [nickname, setNickname] = useState(initial?.nickname ?? "");
  const [title, setTitle] = useState(initial?.title ?? "");
  const [body, setBody] = useState(initial?.body ?? "");
  const [paidPrice, setPaidPrice] = useState(initial?.paid_price != null ? String(initial.paid_price) : "");
  const [feeling, setFeeling] = useState<PriceFeeling | null>(initial?.price_feeling ?? null);
  const [rating, setRating] = useState<number | null>(initial?.rating ?? null);
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!store || (store.kind === "new" && !store.store.name.trim())) {
      setError(t.review.storeRequired);
      return;
    }
    if (props.mode === "create") {
      const pwErr = passwordError(password);
      if (pwErr) {
        setError(pwErr === "short" ? t.review.passwordShort : t.review.passwordLong);
        return;
      }
    }

    const fields: ReviewFields = {
      nickname: nickname.trim() || null,
      title: title.trim(),
      body: body.trim(),
      paid_price: paidPrice === "" ? null : Number(paidPrice),
      price_feeling: feeling,
      rating,
    };
    const storeRef: StoreRef =
      store.kind === "existing" ? { store_id: store.store.id } : { store: { ...store.store, name: store.store.name.trim() } };

    setSaving(true);
    try {
      if (props.mode === "create") {
        const created = await createReview({ ...fields, ...storeRef, password });
        router.push(`/reviews/${created.id}`);
      } else {
        // Only send the store when it changed, so an edit doesn't touch the tag needlessly.
        const storeChanged = store.kind === "new" || store.store.id !== props.review.store?.id;
        const saved = await updateReview(props.review.id, {
          ...fields,
          ...(storeChanged ? storeRef : {}),
          password: props.password,
        });
        props.onSaved(saved);
      }
    } catch (err) {
      setError((err as Error).message);
      setSaving(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-4">
      <Field label={t.review.store}>
        <StorePicker value={store} onChange={setStore} />
      </Field>

      <Field label={t.review.title}>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
          maxLength={LIMITS.title}
          className={inputClass}
        />
      </Field>

      <Field label={t.review.body}>
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          required
          maxLength={LIMITS.body}
          rows={6}
          placeholder={t.review.bodyPlaceholder}
          className={`${inputClass} resize-y`}
        />
      </Field>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label={t.review.paidPrice}>
          <input
            type="number"
            inputMode="numeric"
            min={0}
            step={1}
            value={paidPrice}
            onChange={(e) => setPaidPrice(e.target.value)}
            placeholder="₩"
            className={inputClass}
          />
        </Field>
        <Field label={t.review.nickname}>
          <input
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            maxLength={LIMITS.nickname}
            placeholder={t.review.nicknamePlaceholder}
            className={inputClass}
          />
        </Field>
      </div>

      <fieldset className="flex flex-col gap-1 text-sm font-medium text-slate-700">
        <legend className="mb-1">{t.review.priceFeeling}</legend>
        <div className="flex flex-wrap gap-2">
          {PRICE_FEELINGS.map((f) => (
            <button
              key={f}
              type="button"
              aria-pressed={feeling === f}
              onClick={() => setFeeling(feeling === f ? null : f)}
              className={`rounded-full border px-3 py-1.5 text-sm ${
                feeling === f ? "border-brand bg-brand text-white" : "border-slate-300 bg-white text-slate-700"
              }`}
            >
              {t.priceFeeling[f]}
            </button>
          ))}
        </div>
      </fieldset>

      <fieldset className="flex flex-col gap-1 text-sm font-medium text-slate-700">
        <legend className="mb-1">{t.review.rating}</legend>
        <div className="flex items-center gap-1 text-2xl">
          {[1, 2, 3, 4, 5].map((n) => (
            <button
              key={n}
              type="button"
              aria-label={`${n}`}
              onClick={() => setRating(rating === n ? null : n)}
              className={rating != null && n <= rating ? "text-amber-500" : "text-slate-300"}
            >
              ★
            </button>
          ))}
          {rating == null && <span className="ml-2 text-xs font-normal text-slate-500">{t.review.none}</span>}
        </div>
      </fieldset>

      {props.mode === "create" && (
        <Field label={t.review.password} hint={t.review.passwordHint}>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={LIMITS.passwordMin}
            autoComplete="new-password"
            className={inputClass}
          />
        </Field>
      )}

      {error && <p className="whitespace-pre-line rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}

      <div className="flex justify-end gap-2">
        <button
          type="button"
          onClick={() => (props.mode === "edit" ? props.onCancel() : router.back())}
          className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm"
        >
          {t.review.cancel}
        </button>
        <button
          type="submit"
          disabled={saving}
          className="rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {saving ? t.review.saving : props.mode === "create" ? t.review.submit : t.review.save}
        </button>
      </div>
    </form>
  );
}
