"use client";

import Link from "next/link";
import { Suspense } from "react";

import { PageShell } from "@/components/PageShell";
import { ReviewList } from "@/components/reviews/ReviewList";
import { useT } from "@/lib/i18n";

export default function ReviewsPage() {
  const t = useT();
  return (
    <PageShell
      title={t.review.pageTitle}
      description={t.review.pageDesc}
      action={
        <Link
          href="/reviews/new"
          className="shrink-0 rounded-lg bg-brand px-4 py-2 text-sm font-medium text-slate-900 hover:bg-brand/90"
        >
          {t.review.write}
        </Link>
      }
    >
      {/* ReviewList reads ?q=&page= (useSearchParams), which needs a Suspense boundary under cacheComponents */}
      <Suspense fallback={<p className="py-10 text-center text-slate-500">{t.review.loading}</p>}>
        <ReviewList />
      </Suspense>
    </PageShell>
  );
}
