import { SearchIcon } from "@/components/icons/SearchIcon";
import { t } from "@/lib/strings";

// F1 — plain GET form to /search, backend fills it in later.
export function SearchBar() {
  return (
    <form action="/search" className="flex items-center gap-2 rounded-full bg-white px-5 py-3">
      <input
        name="q"
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
