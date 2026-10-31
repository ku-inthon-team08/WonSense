"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

import { ErrorBox } from "@/components/ErrorBox";
import { listReviews } from "@/lib/reviews";
import { useT } from "@/lib/i18n";
import { inputClass } from "@/lib/ui";
import { useApi } from "@/lib/useApi";

import { ReviewCard } from "./ReviewCard";

const PAGE_SIZE = 10;

// Search term and page live in the URL (?q=&page=) so results can be linked to, e.g. from F1 search.
export function ReviewList() {
  const t = useT();
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const q = params.get("q") ?? "";
  const page = Math.max(1, Number(params.get("page")) || 1);

  const [reload, setReload] = useState(0);
  const { data, error, loading } = useApi(`reviews:${q}|${page}|${reload}`, (signal) =>
    listReviews({ q, page, size: PAGE_SIZE }, { signal }),
  );

  function go(next: { q?: string; page?: number }) {
    const qs = new URLSearchParams();
    const nq = next.q ?? q;
    const np = next.page ?? 1;
    if (nq) qs.set("q", nq);
    if (np > 1) qs.set("page", String(np));
    const s = qs.toString();
    router.push(s ? `${pathname}?${s}` : pathname);
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <div>
      {/* key={q}: reset the input when the URL's search term changes (back/forward, links) */}
      <SearchForm key={q} initial={q} onSearch={(term) => go({ q: term, page: 1 })} />

      <div className="mt-4">
        {loading && <p className="py-10 text-center text-slate-500">{t.review.loading}</p>}

        {error && (
          <ErrorBox title={t.review.loadError} message={error.message}>
            <button onClick={() => setReload((n) => n + 1)} className="mt-2 font-medium underline">
              {t.review.retry}
            </button>
          </ErrorBox>
        )}

        {data && (
          <>
            <p className="mb-2 text-sm text-slate-500">{t.review.total(data.total)}</p>
            {data.items.length === 0 ? (
              <div className="rounded-xl border border-dashed border-slate-300 p-10 text-center text-slate-500">
                {q ? t.review.noResults(q) : t.reviewEmpty}
              </div>
            ) : (
              <ul className="flex flex-col gap-3">
                {data.items.map((r) => (
                  <li key={r.id}>
                    <ReviewCard review={r} />
                  </li>
                ))}
              </ul>
            )}

            {totalPages > 1 && (
              <nav className="mt-6 flex items-center justify-center gap-3 text-sm">
                <button
                  disabled={page <= 1}
                  onClick={() => go({ page: page - 1 })}
                  className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 disabled:opacity-40"
                >
                  {t.review.prev}
                </button>
                <span className="text-slate-600">
                  {page} / {totalPages}
                </span>
                <button
                  disabled={page >= totalPages}
                  onClick={() => go({ page: page + 1 })}
                  className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 disabled:opacity-40"
                >
                  {t.review.next}
                </button>
              </nav>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function SearchForm({ initial, onSearch }: { initial: string; onSearch: (q: string) => void }) {
  const t = useT();
  const [input, setInput] = useState(initial);
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSearch(input.trim());
      }}
      className="flex gap-2"
    >
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder={t.review.searchPlaceholder}
        aria-label={t.review.search}
        className={inputClass}
      />
      <button type="submit" className="shrink-0 rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white">
        {t.review.search}
      </button>
    </form>
  );
}
