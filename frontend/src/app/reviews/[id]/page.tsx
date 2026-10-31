import Link from "next/link";
import { Suspense } from "react";

import { ReviewDetail } from "@/components/reviews/ReviewDetail";
import { t } from "@/lib/strings";

export default function ReviewPage() {
  return (
    <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-6">
      <Link href="/reviews" className="text-sm text-indigo-600">{t.review.backToList}</Link>
      <div className="mt-2">
        {/* The id is only known at request time, so useParams() needs a Suspense boundary */}
        <Suspense fallback={<p className="py-10 text-center text-slate-500">{t.review.loading}</p>}>
          <ReviewDetail />
        </Suspense>
      </div>
    </main>
  );
}
