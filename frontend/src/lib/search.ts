// F1 price search — types and calls for backend/app/routers/items.py
import { api } from "@/lib/api";

export type SearchItem = {
  item_id: number;
  name_ko: string;
  name_en: string | null;
  category: string;
  unit: string;
  // Seoul-wide: cheapest / average / priciest of the 25 district averages
  price_min: number;
  price_avg: number;
  price_max: number;
  district_count: number;
  source: string;
  reference_date: string;
};

// Restaurant menu / service prices from Seoul's "good price" stores (cheaper than typical)
export type MenuExample = { store_name: string; menu_name: string; price: number; district: string | null };
export type MenuResult = {
  name_ko: string;
  name_en: string | null;
  count: number; // menu rows matched
  store_count: number;
  price_low: number; // 25th percentile — "usually" range
  price_median: number;
  price_high: number; // 75th percentile
  price_min: number;
  price_max: number;
  examples: MenuExample[];
  source: string;
  reference_date: string | null;
};

export type SearchResponse = {
  query: string;
  results: SearchItem[];
  menus: MenuResult[];
  suggestions: string[]; // typo fixes when there are no results
  not_covered: boolean; // restaurant menu / transport query: no data yet
};

export const searchItems = (q: string, init?: RequestInit) =>
  api<SearchResponse>(`/api/items/search?q=${encodeURIComponent(q)}`, init);
