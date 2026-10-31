import Link from "next/link";
import { Suspense } from "react";

import { SearchResults } from "@/components/search/SearchResults";
import { t } from "@/lib/strings";

export default function SearchPage() {
  return (
    <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-6">
      <Link href="/" className="text-sm text-brand">{t.home}</Link>
      <h1 className="mt-2 text-2xl font-bold">{t.search.pageTitle}</h1>
      <p className="mt-1 text-sm text-slate-500">{t.search.pageDesc}</p>
      <div className="mt-6">
        {/* SearchResults reads ?q= (useSearchParams), which needs a Suspense boundary */}
        <Suspense fallback={<p className="py-10 text-center text-slate-500">{t.loading}</p>}>
          <SearchResults />
        </Suspense>
      </div>
    </main>
  );
}
