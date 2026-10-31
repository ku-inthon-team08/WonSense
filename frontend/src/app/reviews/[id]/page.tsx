"use client";

import Link from "next/link";
import { Suspense } from "react";

import { PageShell } from "@/components/PageShell";
import { ReviewDetail } from "@/components/reviews/ReviewDetail";
import { useT } from "@/lib/i18n";

export default function ReviewPage() {
  const t = useT();
  return (
    <PageShell back={<Link href="/reviews">{t.review.backToList}</Link>}>
      {/* The id is only known at request time, so useParams() needs a Suspense boundary */}
      <Suspense fallback={<p className="py-10 text-center text-slate-500">{t.review.loading}</p>}>
        <ReviewDetail />
      </Suspense>
    </PageShell>
  );
}
