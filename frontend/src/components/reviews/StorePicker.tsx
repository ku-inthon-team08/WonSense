"use client";

import { useEffect, useState } from "react";

import { DISTRICTS, STORE_CATEGORIES, searchStores, type NewStore, type Store, type StoreCategory } from "@/lib/reviews";
import { t } from "@/lib/strings";

import { StoreTag } from "./ReviewMeta";

export type StoreChoice = { kind: "existing"; store: Store } | { kind: "new"; store: NewStore } | null;

const inputClass = "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 outline-none focus:border-brand";

// Pick an existing store (autocomplete on GET /api/stores) or describe a new one.
// The backend reuses a store with the same name + district, so duplicates are harmless.
export function StorePicker({ value, onChange }: { value: StoreChoice; onChange: (v: StoreChoice) => void }) {
  const [query, setQuery] = useState("");
  const [found, setFound] = useState<{ q: string; stores: Store[] }>({ q: "", stores: [] });
  const [open, setOpen] = useState(false);
  const name = query.trim();
  // Only show results for the term currently typed (older responses are ignored).
  const results = found.q === name ? found.stores : [];

  useEffect(() => {
    if (!name) return;
    let cancelled = false;
    const timer = setTimeout(() => {
      searchStores(name)
        .then((stores) => !cancelled && setFound({ q: name, stores }))
        .catch(() => !cancelled && setFound({ q: name, stores: [] }));
    }, 250);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [name]);

  if (value?.kind === "existing") {
    return (
      <div className="flex items-center justify-between gap-2 rounded-lg border border-slate-300 bg-slate-50 px-3 py-2">
        <StoreTag store={value.store} />
        <button type="button" onClick={() => onChange(null)} className="text-sm text-brand">
          {t.review.storeChange}
        </button>
      </div>
    );
  }

  if (value?.kind === "new") {
    const set = (patch: Partial<NewStore>) => onChange({ kind: "new", store: { ...value.store, ...patch } });
    return (
      <div className="flex flex-col gap-2 rounded-lg border border-slate-300 bg-slate-50 p-3">
        <div className="flex items-center gap-2">
          <input
            value={value.store.name}
            onChange={(e) => set({ name: e.target.value })}
            maxLength={100}
            aria-label={t.review.store}
            className={inputClass}
          />
          <button type="button" onClick={() => onChange(null)} className="shrink-0 text-sm text-brand">
            {t.review.storeChange}
          </button>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <label className="text-xs text-slate-600">
            {t.review.storeCategory}
            <select
              value={value.store.category}
              onChange={(e) => set({ category: e.target.value as StoreCategory })}
              className={`${inputClass} mt-1 text-sm`}
            >
              {STORE_CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {t.storeCategory[c]}
                </option>
              ))}
            </select>
          </label>
          <label className="text-xs text-slate-600">
            {t.review.storeDistrict}
            <select
              value={value.store.district ?? ""}
              onChange={(e) => set({ district: e.target.value || null })}
              className={`${inputClass} mt-1 text-sm`}
            >
              <option value="">{t.review.storeDistrictNone}</option>
              {DISTRICTS.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </label>
        </div>
        <input
          value={value.store.address ?? ""}
          onChange={(e) => set({ address: e.target.value || null })}
          placeholder={t.review.storeAddress}
          maxLength={200}
          className={`${inputClass} text-sm`}
        />
      </div>
    );
  }

  return (
    <div className="relative">
      <input
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        placeholder={t.review.storeSearch}
        aria-label={t.review.store}
        className={inputClass}
      />
      {open && name && (
        <ul className="absolute z-10 mt-1 max-h-64 w-full overflow-auto rounded-lg border border-slate-200 bg-white shadow-lg">
          {results.map((s) => (
            <li key={s.id}>
              <button
                type="button"
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => onChange({ kind: "existing", store: s })}
                className="w-full px-3 py-2 text-left hover:bg-brand-pale"
              >
                <StoreTag store={s} />
              </button>
            </li>
          ))}
          <li className="border-t border-slate-100">
            <button
              type="button"
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => onChange({ kind: "new", store: { name, category: "restaurant", district: null } })}
              className="w-full px-3 py-2 text-left text-sm font-medium text-brand hover:bg-brand-pale"
            >
              + {t.review.storeNew(name)}
            </button>
          </li>
        </ul>
      )}
    </div>
  );
}
