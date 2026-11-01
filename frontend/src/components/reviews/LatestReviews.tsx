"use client";

import Link from "next/link";

import { listReviews } from "@/lib/reviews";
import { useT } from "@/lib/i18n";
import { useApi } from "@/lib/useApi";

import { ReviewCard } from "./ReviewCard";
import { SkeletonRows } from "@/components/Skeleton";

// Home ④: the newest few reviews.
export function LatestReviews({ count = 3 }: { count?: number }) {
  const t = useT();
  const { data, error } = useApi(`latest-reviews:${count}`, (signal) => listReviews({ size: count }, { signal }));
  const reviews = data?.items;

  if (error) return <p className="py-4 text-center text-sm text-slate-500">{t.review.loadError}</p>;
  if (!reviews) return <SkeletonRows label={t.review.loading} rows={count} />;
  if (reviews.length === 0)
    return (
      <Link
        href="/reviews/new"
        className="block rounded-xl border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500 hover:border-brand/50"
      >
        {t.reviewEmpty} · <span className="text-brand-ink">{t.review.write}</span>
      </Link>
    );

  return (
    <ul className="flex flex-col divide-y divide-slate-100 [&>li]:py-2 [&>li:first-child]:pt-0">
      {reviews.map((r) => (
        <li key={r.id}>
          <ReviewCard review={r} compact />
        </li>
      ))}
    </ul>
  );
}
