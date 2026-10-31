import { t } from "@/lib/strings";

// F1 — plain GET form to /search (results page reads ?q=).
export function SearchBar({ defaultValue = "" }: { defaultValue?: string }) {
  return (
    <form action="/search" className="flex items-center gap-2 rounded-full border border-slate-300 bg-white px-4 py-2 shadow-sm focus-within:border-indigo-500">
      <input
        name="q"
        defaultValue={defaultValue}
        required
        placeholder={t.searchPlaceholder}
        className="w-full bg-transparent py-1 text-base outline-none"
        aria-label="search"
      />
      <button type="submit" aria-label="search" className="text-xl">🔍</button>
    </form>
  );
}
