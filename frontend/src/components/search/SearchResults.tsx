"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";

import { SearchBar } from "@/components/SearchBar";
import { formatKrw } from "@/lib/reviews";
import { searchItems, type MenuResult, type SearchItem } from "@/lib/search";
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

        {data && data.menus.length > 0 && (
          <section className="mb-8">
            <h2 className="mb-1 font-semibold text-slate-800">{t.search.menusTitle}</h2>
            <p className="mb-3 text-xs text-slate-500">{t.search.menusNote}</p>
            <ul className="flex flex-col gap-3">
              {data.menus.map((menu) => (
                <li key={menu.name_ko}>
                  <MenuCard menu={menu} />
                </li>
              ))}
            </ul>
          </section>
        )}

        {data && data.results.length > 0 && (
          <>
            {data.menus.length > 0 && <h2 className="mb-1 font-semibold text-slate-800">{t.search.groceriesTitle}</h2>}
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

        {data && data.results.length === 0 && data.menus.length > 0 && <ReviewLink q={q} />}

        {data && data.results.length === 0 && data.menus.length === 0 && (
          <div className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-slate-600">
            <p>{t.search.noResults(q)}</p>
            {data.not_covered && <p className="mt-2 text-sm text-slate-500">{t.search.notCovered}</p>}
            {data.suggestions.length > 0 && (
              <p className="mt-3 text-sm">
                {t.search.didYouMean}{" "}
                {data.suggestions.map((s, i) => (
                  <span key={s}>
                    {i > 0 && ", "}
                    <Link href={`/search?q=${encodeURIComponent(s)}`} className="font-medium text-brand underline">
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
    <article className="rounded-xl bg-white p-4 shadow-card">
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

function MenuCard({ menu }: { menu: MenuResult }) {
  return (
    <article className="rounded-xl bg-white p-4 shadow-card">
      <h3 className="font-semibold text-slate-900">
        {menu.name_en ?? menu.name_ko}
        {menu.name_en && <span className="ml-2 text-sm font-normal text-slate-500">{menu.name_ko}</span>}
      </h3>
      <p className="mt-2 text-slate-800">
        {t.search.usually}{" "}
        <strong className="text-lg">
          {menu.price_low === menu.price_high
            ? formatKrw(menu.price_median)
            : `${formatKrw(menu.price_low)} ~ ${formatKrw(menu.price_high)}`}
        </strong>
      </p>
      <p className="text-sm text-slate-600">
        {t.search.median} <strong>{formatKrw(menu.price_median)}</strong> ·{" "}
        {t.search.menuRange(formatKrw(menu.price_min), formatKrw(menu.price_max))}
      </p>
      {menu.examples.length > 0 && (
        <ul className="mt-3 divide-y divide-slate-100 text-sm">
          {menu.examples.map((e) => (
            <li key={`${e.store_name}-${e.menu_name}`} className="flex items-baseline justify-between gap-2 py-1.5">
              <span className="min-w-0 truncate">
                {e.store_name}
                <span className="ml-1 text-xs text-slate-500">
                  {e.menu_name}
                  {e.district && ` · ${e.district}`}
                </span>
              </span>
              <span className="shrink-0 font-medium tabular-nums">{formatKrw(e.price)}</span>
            </li>
          ))}
        </ul>
      )}
      <p className="mt-2 text-xs text-slate-500">
        {t.search.source}: {menu.source}
        {menu.reference_date && ` · ${t.search.referenceDate} ${menu.reference_date}`} ·{" "}
        {t.search.stores(menu.store_count)}
      </p>
    </article>
  );
}

function ReviewLink({ q }: { q: string }) {
  return (
    <Link href={`/reviews?q=${encodeURIComponent(q)}`} className="mt-4 inline-block text-sm font-medium text-brand">
      {t.search.reviews(q)} →
    </Link>
  );
}
