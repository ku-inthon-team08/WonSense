"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { listReviews, type Review } from "@/lib/reviews";
import { t } from "@/lib/strings";

import { ReviewCard } from "./ReviewCard";

// Home ④: the newest few reviews.
export function LatestReviews({ count = 3 }: { count?: number }) {
  const [reviews, setReviews] = useState<Review[] | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    listReviews({ size: count })
      .then((p) => setReviews(p.items))
      .catch(() => setFailed(true));
  }, [count]);

  if (failed) return <p className="py-4 text-center text-sm text-slate-500">{t.review.loadError}</p>;
  if (!reviews) return <p className="py-4 text-center text-sm text-slate-500">{t.review.loading}</p>;
  if (reviews.length === 0)
    return (
      <Link
        href="/reviews/new"
        className="block rounded-xl border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500 hover:border-indigo-300"
      >
        {t.reviewEmpty} · <span className="text-indigo-600">{t.review.write}</span>
      </Link>
    );

  return (
    <ul className="flex flex-col gap-2">
      {reviews.map((r) => (
        <li key={r.id}>
          <ReviewCard review={r} compact />
        </li>
      ))}
    </ul>
  );
}
