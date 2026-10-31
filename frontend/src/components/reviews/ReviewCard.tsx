"use client";

import Link from "next/link";

import { formatDate, formatKrw } from "@/lib/format";
import type { Review } from "@/lib/reviews";
import { useT } from "@/lib/i18n";

import { CategoryTile, PriceFeelingBadge, Stars, StoreTag } from "./ReviewMeta";

// compact: 홈 리뷰 카드 안의 한 줄 (왼쪽 가게 종류 그림, 그림자 없이 구분선으로 나눈다). 기본: 리뷰 목록 페이지의 카드.
export function ReviewCard({ review, compact = false }: { review: Review; compact?: boolean }) {
  const t = useT();
  const meta = (
    <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-500">
      {review.paid_price != null && (
        <span className="font-medium text-slate-800">
          {t.review.paid} {formatKrw(review.paid_price)}
        </span>
      )}
      {review.price_feeling && <PriceFeelingBadge feeling={review.price_feeling} />}
      <span className="ml-auto">
        {review.nickname} · {formatDate(review.created_at, t.dateLocale)}
      </span>
    </div>
  );

  if (compact)
    return (
      <Link href={`/reviews/${review.id}`} className="-mx-2 flex gap-4 rounded-2xl p-2 transition hover:bg-brand-pale">
        <CategoryTile category={review.store?.category} />
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-3">
            <h3 className="font-semibold text-slate-900 line-clamp-1">{review.title}</h3>
            {review.rating != null && <Stars rating={review.rating} />}
          </div>
          {review.store && (
            <div className="mt-0.5 truncate">
              <StoreTag store={review.store} />
            </div>
          )}
          {meta}
        </div>
      </Link>
    );

  return (
    <Link
      href={`/reviews/${review.id}`}
      className="block rounded-xl bg-white p-4 shadow-card transition hover:ring-1 hover:ring-brand/50"
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
      <p className="mt-2 text-sm text-slate-600 line-clamp-2 whitespace-pre-line">{review.body}</p>
      <div className="mt-1">{meta}</div>
    </Link>
  );
}
