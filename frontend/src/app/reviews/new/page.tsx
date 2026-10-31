import Link from "next/link";

import { PageShell } from "@/components/PageShell";
import { ReviewForm } from "@/components/reviews/ReviewForm";
import { t } from "@/lib/strings";
import { card } from "@/lib/ui";

export default function NewReviewPage() {
  return (
    <PageShell title={t.review.newTitle} back={<Link href="/reviews">{t.review.backToList}</Link>}>
      <section className={card}>
        <ReviewForm mode="create" />
      </section>
    </PageShell>
  );
}
