import Link from "next/link";
import { Suspense } from "react";

import { ReviewList } from "@/components/reviews/ReviewList";
import { t } from "@/lib/strings";

export default function ReviewsPage() {
  return (
    <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-6">
      <Link href="/" className="text-sm text-brand">{t.home}</Link>
      <div className="mt-2 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">{t.review.pageTitle}</h1>
          <p className="mt-1 text-sm text-slate-500">{t.review.pageDesc}</p>
        </div>
        <Link
          href="/reviews/new"
          className="shrink-0 rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand/90"
        >
          {t.review.write}
        </Link>
      </div>
      <div className="mt-6">
        {/* ReviewList reads ?q=&page= (useSearchParams), which needs a Suspense boundary under cacheComponents */}
        <Suspense fallback={<p className="py-10 text-center text-slate-500">{t.review.loading}</p>}>
          <ReviewList />
        </Suspense>
      </div>
    </main>
  );
}
