"use client";

import { SearchIcon } from "@/components/icons/SearchIcon";
import { useT } from "@/lib/i18n";

// F1 — plain GET form to /search (results page reads ?q=).
// 흰 알약 모양: 왼쪽 돋보기 아이콘, 오른쪽 둥근 brand 검색 버튼.
export function SearchBar({ defaultValue = "" }: { defaultValue?: string }) {
  const t = useT();
  return (
    <form
      action="/search"
      className="flex items-center gap-3 rounded-full bg-white py-1.5 pl-5 pr-1.5 shadow-card ring-1 ring-brand/10 focus-within:ring-2 focus-within:ring-brand/60"
    >
      <SearchIcon className="h-5 w-5 shrink-0 text-slate-400" />
      <input
        name="q"
        defaultValue={defaultValue}
        required
        placeholder={t.searchPlaceholder}
        className="min-w-0 flex-1 bg-transparent py-2 text-base outline-none placeholder:text-slate-400"
        aria-label={t.searchLabel}
      />
      <button
        type="submit"
        aria-label={t.searchLabel}
        className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-brand text-slate-900 transition hover:brightness-95 active:scale-95"
      >
        <SearchIcon className="h-5 w-5" />
      </button>
    </form>
  );
}
