"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { listReviews, type ReviewPage } from "@/lib/reviews";
import { t } from "@/lib/strings";

import { ReviewCard } from "./ReviewCard";

const PAGE_SIZE = 10;

type State = { status: "loading" } | { status: "error"; message: string } | { status: "ok"; data: ReviewPage };
type Result = { key: string; state: State };

// Search term and page live in the URL (?q=&page=) so results can be linked to, e.g. from F1 search.
export function ReviewList() {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const q = params.get("q") ?? "";
  const page = Math.max(1, Number(params.get("page")) || 1);

  const [reload, setReload] = useState(0);
  const [result, setResult] = useState<Result | null>(null);

  // A result belongs to one (q, page, reload) request; anything else means we're still loading.
  const key = `${q}|${page}|${reload}`;
  const state: State = result?.key === key ? result.state : { status: "loading" };

  useEffect(() => {
    let cancelled = false;
    listReviews({ q, page, size: PAGE_SIZE })
      .then((data) => !cancelled && setResult({ key, state: { status: "ok", data } }))
      .catch((e: Error) => !cancelled && setResult({ key, state: { status: "error", message: e.message } }));
    return () => {
      cancelled = true;
    };
  }, [key, q, page]);

  function go(next: { q?: string; page?: number }) {
    const qs = new URLSearchParams();
    const nq = next.q ?? q;
    const np = next.page ?? 1;
    if (nq) qs.set("q", nq);
    if (np > 1) qs.set("page", String(np));
    const s = qs.toString();
    router.push(s ? `${pathname}?${s}` : pathname);
  }

  const totalPages = state.status === "ok" ? Math.max(1, Math.ceil(state.data.total / PAGE_SIZE)) : 1;

  return (
    <div>
      {/* key={q}: reset the input when the URL's search term changes (back/forward, links) */}
      <SearchForm key={q} initial={q} onSearch={(term) => go({ q: term, page: 1 })} />

      <div className="mt-4">
        {state.status === "loading" && <p className="py-10 text-center text-slate-500">{t.review.loading}</p>}

        {state.status === "error" && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
            <p>{t.review.loadError}</p>
            <p className="mt-1 text-xs opacity-80">{state.message}</p>
            <button onClick={() => setReload((n) => n + 1)} className="mt-2 font-medium underline">
              {t.review.retry}
            </button>
          </div>
        )}

        {state.status === "ok" && (
          <>
            <p className="mb-2 text-sm text-slate-500">{t.review.total(state.data.total)}</p>
            {state.data.items.length === 0 ? (
              <div className="rounded-xl border border-dashed border-slate-300 p-10 text-center text-slate-500">
                {q ? t.review.noResults(q) : t.reviewEmpty}
              </div>
            ) : (
              <ul className="flex flex-col gap-3">
                {state.data.items.map((r) => (
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
        className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 outline-none focus:border-brand"
      />
      <button type="submit" className="shrink-0 rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white">
        {t.review.search}
      </button>
    </form>
  );
}
