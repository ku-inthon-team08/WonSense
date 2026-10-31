"use client";

import Link from "next/link";

import { PageShell } from "@/components/PageShell";
import { ReviewForm } from "@/components/reviews/ReviewForm";
import { useT } from "@/lib/i18n";
import { card } from "@/lib/ui";

export default function NewReviewPage() {
  const t = useT();
  return (
    <PageShell title={t.review.newTitle} back={<Link href="/reviews">{t.review.backToList}</Link>}>
      <section className={card}>
        <ReviewForm mode="create" />
      </section>
    </PageShell>
  );
}
