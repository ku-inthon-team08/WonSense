"use client";

import { SearchIcon } from "@/components/icons/SearchIcon";
import { useT } from "@/lib/i18n";

// F1 — plain GET form to /search (results page reads ?q=).
export function SearchBar({ defaultValue = "" }: { defaultValue?: string }) {
  const t = useT();
  return (
    <form action="/search" className="flex items-center gap-2 rounded-full bg-white px-5 py-3">
      <input
        name="q"
        defaultValue={defaultValue}
        required
        placeholder={t.searchPlaceholder}
        className="w-full bg-transparent py-1 text-base outline-none"
        aria-label="search"
      />
      <button type="submit" aria-label="search" className="text-brand">
        <SearchIcon className="h-6 w-6" />
      </button>
    </form>
  );
}
