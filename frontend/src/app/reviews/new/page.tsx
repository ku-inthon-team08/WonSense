import Link from "next/link";

import { ReviewForm } from "@/components/reviews/ReviewForm";
import { t } from "@/lib/strings";

export default function NewReviewPage() {
  return (
    <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-6">
      <Link href="/reviews" className="text-sm text-brand">{t.review.backToList}</Link>
      <section className="mt-2 rounded-2xl bg-white p-5 shadow-card">
        <h1 className="mb-4 text-xl font-bold">{t.review.newTitle}</h1>
        <ReviewForm mode="create" />
      </section>
    </main>
  );
}
