"use client";

import { Suspense } from "react";

import { PageShell } from "@/components/PageShell";
import { SearchResults } from "@/components/search/SearchResults";
import { useT } from "@/lib/i18n";

export default function SearchPage() {
  const t = useT();
  return (
    <PageShell title={t.search.pageTitle} description={t.search.pageDesc}>
      {/* SearchResults reads ?q= (useSearchParams), which needs a Suspense boundary */}
      <Suspense fallback={<p className="py-10 text-center text-slate-500">{t.loading}</p>}>
        <SearchResults />
      </Suspense>
    </PageShell>
  );
}
