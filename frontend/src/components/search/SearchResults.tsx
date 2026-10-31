"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";

import { SearchBar } from "@/components/SearchBar";
import { formatKrw } from "@/lib/reviews";
import { searchItems, type SearchItem } from "@/lib/search";
import { t } from "@/lib/strings";
import { useApi } from "@/lib/useApi";

// Reads ?q= so results can be linked to and the browser back button works.
export function SearchResults() {
  const q = (useSearchParams().get("q") ?? "").trim();
  const { data, error, loading } = useApi(q ? `search:${q}` : null, (signal) => searchItems(q, { signal }));

  return (
    <div>
      {/* key={q}: reset the input when the URL's search term changes */}
      <SearchBar key={q} defaultValue={q} />

      <div className="mt-6">
        {!q && <p className="py-10 text-center text-slate-500">{t.search.empty}</p>}
        {loading && <p className="py-10 text-center text-slate-500">{t.loading}</p>}
        {error && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
            <p>{t.search.error}</p>
            <p className="mt-1 text-xs opacity-80">{error.message}</p>
          </div>
        )}

        {data && data.results.length > 0 && (
          <>
            <p className="mb-2 text-sm text-slate-500">{t.search.count(data.results.length)}</p>
            <ul className="flex flex-col gap-3">
              {data.results.map((item) => (
                <li key={item.item_id}>
                  <ResultCard item={item} />
                </li>
              ))}
            </ul>
            <p className="mt-4 text-xs text-slate-500">{t.search.rangeNote}</p>
            <ReviewLink q={q} />
          </>
        )}

        {data && data.results.length === 0 && (
          <div className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-slate-600">
            <p>{t.search.noResults(q)}</p>
            {data.not_covered && <p className="mt-2 text-sm text-slate-500">{t.search.notCovered}</p>}
            {data.suggestions.length > 0 && (
              <p className="mt-3 text-sm">
                {t.search.didYouMean}{" "}
                {data.suggestions.map((s, i) => (
                  <span key={s}>
                    {i > 0 && ", "}
                    <Link href={`/search?q=${encodeURIComponent(s)}`} className="font-medium text-indigo-600 underline">
                      {s}
                    </Link>
                  </span>
                ))}
              </p>
            )}
            <ReviewLink q={q} />
          </div>
        )}
      </div>
    </div>
  );
}

function ResultCard({ item }: { item: SearchItem }) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
        <h2 className="font-semibold text-slate-900">
          {item.name_en ?? item.name_ko}
          {item.name_en && <span className="ml-2 text-sm font-normal text-slate-500">{item.name_ko}</span>}
        </h2>
        <span className="text-xs text-slate-500">{item.unit}</span>
      </div>
      <p className="mt-2 text-slate-800">
        {t.search.usually}{" "}
        <strong className="text-lg">
          {formatKrw(item.price_min)} ~ {formatKrw(item.price_max)}
        </strong>
      </p>
      <p className="text-sm text-slate-600">
        {t.search.average} <strong>{formatKrw(item.price_avg)}</strong>
      </p>
      <p className="mt-2 text-xs text-slate-500">
        {t.search.source}: {item.source} · {t.search.referenceDate} {item.reference_date} ·{" "}
        {t.search.districts(item.district_count)}
      </p>
    </article>
  );
}

function ReviewLink({ q }: { q: string }) {
  return (
    <Link href={`/reviews?q=${encodeURIComponent(q)}`} className="mt-4 inline-block text-sm font-medium text-indigo-600">
      {t.search.reviews(q)} →
    </Link>
  );
}
