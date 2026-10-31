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

// Vercel(프론트)와 Render(백엔드)는 따로 배포되므로, 프론트가 먼저 바뀌면 백엔드 응답에 menus가 아직 없을 수 있다.
// 그때도 화면이 깨지지 않도록 빠진 배열은 빈 배열로 채운다.
export const searchItems = async (q: string, init?: RequestInit): Promise<SearchResponse> => {
  const res = await api<Partial<SearchResponse>>(`/api/items/search?q=${encodeURIComponent(q)}`, init);
  return {
    query: res.query ?? q,
    results: res.results ?? [],
    menus: res.menus ?? [],
    suggestions: res.suggestions ?? [],
    not_covered: res.not_covered ?? false,
  };
};
