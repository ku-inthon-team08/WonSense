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

export type SearchResponse = {
  query: string;
  results: SearchItem[];
  suggestions: string[]; // typo fixes when there are no results
  not_covered: boolean; // restaurant menu / transport query: no data yet
};

export const searchItems = (q: string, init?: RequestInit) =>
  api<SearchResponse>(`/api/items/search?q=${encodeURIComponent(q)}`, init);
