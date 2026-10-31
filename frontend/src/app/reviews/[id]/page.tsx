"use client";

import Link from "next/link";
import { Suspense } from "react";

import { ReviewDetail } from "@/components/reviews/ReviewDetail";
import { useT } from "@/lib/i18n";

export default function ReviewPage() {
  const t = useT();
  return (
    <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-6">
      <Link href="/reviews" className="text-sm text-brand">{t.review.backToList}</Link>
      <div className="mt-2">
        {/* The id is only known at request time, so useParams() needs a Suspense boundary */}
        <Suspense fallback={<p className="py-10 text-center text-slate-500">{t.review.loading}</p>}>
          <ReviewDetail />
        </Suspense>
      </div>
    </main>
  );
}
