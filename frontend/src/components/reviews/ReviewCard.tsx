import Link from "next/link";

import { formatDate, formatKrw, type Review } from "@/lib/reviews";
import { t } from "@/lib/strings";

import { PriceFeelingBadge, Stars, StoreTag } from "./ReviewMeta";

export function ReviewCard({ review, compact = false }: { review: Review; compact?: boolean }) {
  return (
    <Link
      href={`/reviews/${review.id}`}
      className="block rounded-xl border border-slate-200 bg-white p-4 transition hover:border-indigo-300 hover:shadow-sm"
    >
      <div className="flex items-start justify-between gap-3">
        <h3 className="font-semibold text-slate-900 line-clamp-1">{review.title}</h3>
        {review.rating != null && <Stars rating={review.rating} />}
      </div>
      {review.store && (
        <div className="mt-1">
          <StoreTag store={review.store} />
        </div>
      )}
      {!compact && <p className="mt-2 text-sm text-slate-600 line-clamp-2 whitespace-pre-line">{review.body}</p>}
      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-500">
        {review.paid_price != null && (
          <span className="font-medium text-slate-800">
            {t.review.paid} {formatKrw(review.paid_price)}
          </span>
        )}
        {review.price_feeling && <PriceFeelingBadge feeling={review.price_feeling} />}
        <span className="ml-auto">
          {review.nickname} · {formatDate(review.created_at)}
        </span>
      </div>
    </Link>
  );
}
