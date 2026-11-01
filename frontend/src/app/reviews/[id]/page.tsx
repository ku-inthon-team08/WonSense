"use client";

import Link from "next/link";
import { Suspense } from "react";

import { PageShell } from "@/components/PageShell";
import { ReviewDetail } from "@/components/reviews/ReviewDetail";
import { useT } from "@/lib/i18n";
import { SkeletonCards } from "@/components/Skeleton";

export default function ReviewPage() {
  const t = useT();
  return (
    <PageShell back={<Link href="/reviews">{t.review.backToList}</Link>}>
      {/* The id is only known at request time, so useParams() needs a Suspense boundary */}
      <Suspense fallback={<SkeletonCards label={t.review.loading} cards={1} />}>
        <ReviewDetail />
      </Suspense>
    </PageShell>
  );
}
