"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ApiError } from "@/lib/api";
import {
  deleteReview,
  formatDate,
  formatKrw,
  getReview,
  verifyReviewPassword,
  type Review,
} from "@/lib/reviews";
import { t } from "@/lib/strings";

import { PasswordDialog } from "./PasswordDialog";
import { PriceFeelingBadge, Stars, StoreTag } from "./ReviewMeta";
import { ReviewForm } from "./ReviewForm";

type State =
  | { status: "loading" }
  | { status: "notFound" }
  | { status: "error"; message: string }
  | { status: "ok"; review: Review };

export function ReviewDetail() {
  const { id } = useParams<{ id: string }>();
  const reviewId = Number(id);
  const router = useRouter();

  const validId = Number.isInteger(reviewId) && reviewId > 0;

  const [loaded, setLoaded] = useState<{ id: number; state: State } | null>(null);
  const [dialog, setDialog] = useState<"edit" | "delete" | null>(null);
  const [editPassword, setEditPassword] = useState<string | null>(null);

  const state: State = !validId
    ? { status: "notFound" }
    : loaded?.id === reviewId
      ? loaded.state
      : { status: "loading" };
  const setState = (next: State) => setLoaded({ id: reviewId, state: next });

  useEffect(() => {
    if (!validId) return;
    let cancelled = false;
    getReview(reviewId)
      .then((review) => !cancelled && setLoaded({ id: reviewId, state: { status: "ok", review } }))
      .catch((e: Error) => {
        if (cancelled) return;
        setLoaded({
          id: reviewId,
          state: e instanceof ApiError && e.status === 404 ? { status: "notFound" } : { status: "error", message: e.message },
        });
      });
    return () => {
      cancelled = true;
    };
  }, [reviewId, validId]);

  if (state.status === "loading") return <p className="py-10 text-center text-slate-500">{t.review.loading}</p>;
  if (state.status === "notFound")
    return <p className="py-10 text-center text-slate-500">{t.review.notFound}</p>;
  if (state.status === "error")
    return (
      <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
        <p>{t.review.loadError}</p>
        <p className="mt-1 text-xs opacity-80">{state.message}</p>
      </div>
    );

  const review = state.review;

  if (editPassword) {
    return (
      <section className="rounded-2xl bg-white p-5 shadow-card">
        <h1 className="mb-4 text-xl font-bold">{t.review.editTitle}</h1>
        <ReviewForm
          mode="edit"
          review={review}
          password={editPassword}
          onCancel={() => setEditPassword(null)}
          onSaved={(saved) => {
            setState({ status: "ok", review: saved });
            setEditPassword(null);
          }}
        />
      </section>
    );
  }

  const edited = review.updated_at !== review.created_at;

  return (
    <article className="rounded-2xl bg-white p-5 shadow-card">
      <div className="flex items-start justify-between gap-3">
        <h1 className="text-xl font-bold">{review.title}</h1>
        {review.rating != null && <Stars rating={review.rating} />}
      </div>
      {review.store && (
        <div className="mt-2">
          <Link href={`/reviews?q=${encodeURIComponent(review.store.name)}`}>
            <StoreTag store={review.store} />
          </Link>
        </div>
      )}
      <p className="mt-1 text-xs text-slate-500">
        {review.nickname} · {formatDate(review.created_at)}
        {edited && ` (${t.review.edited})`}
      </p>

      {(review.paid_price != null || review.price_feeling) && (
        <div className="mt-4 flex flex-wrap items-center gap-3 rounded-xl bg-stone-100 px-4 py-3">
          {review.paid_price != null && (
            <span>
              <span className="text-sm text-slate-600">{t.review.paid} </span>
              <span className="text-lg font-bold text-brand">{formatKrw(review.paid_price)}</span>
            </span>
          )}
          {review.price_feeling && <PriceFeelingBadge feeling={review.price_feeling} />}
        </div>
      )}

      <p className="mt-4 whitespace-pre-line leading-relaxed text-slate-800">{review.body}</p>

      <div className="mt-6 flex justify-end gap-2 border-t border-slate-100 pt-4">
        <button onClick={() => setDialog("edit")} className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm">
          {t.review.edit}
        </button>
        <button
          onClick={() => setDialog("delete")}
          className="rounded-lg border border-rose-200 px-3 py-1.5 text-sm text-rose-600"
        >
          {t.review.delete}
        </button>
      </div>

      {dialog === "edit" && (
        <PasswordDialog
          message={t.review.confirmEdit}
          onClose={() => setDialog(null)}
          onConfirm={async (pw) => {
            await verifyReviewPassword(review.id, pw);
            setDialog(null);
            setEditPassword(pw);
          }}
        />
      )}
      {dialog === "delete" && (
        <PasswordDialog
          danger
          message={t.review.confirmDelete}
          onClose={() => setDialog(null)}
          onConfirm={async (pw) => {
            await deleteReview(review.id, pw);
            router.push("/reviews");
          }}
        />
      )}
    </article>
  );
}
