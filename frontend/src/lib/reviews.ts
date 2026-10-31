// F4 review board — types and calls for backend/app/routers/{reviews,stores}.py
import { api } from "@/lib/api";

export const STORE_CATEGORIES = ["restaurant", "cafe", "bar", "convenience", "market", "shop", "other"] as const;
export type StoreCategory = (typeof STORE_CATEGORIES)[number];

export const PRICE_FEELINGS = ["cheap", "fair", "expensive"] as const;
export type PriceFeeling = (typeof PRICE_FEELINGS)[number];

// Same 25 names as the `districts` table (stores.district stores the Korean name).
export const DISTRICTS = [
  "강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구", "노원구",
  "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구", "성북구", "송파구",
  "양천구", "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구",
] as const;

export type Store = {
  id: number;
  name: string;
  category: StoreCategory;
  district: string | null;
  address?: string | null;
};

export type NewStore = {
  name: string;
  category: StoreCategory;
  district?: string | null;
  address?: string | null;
};

export type Review = {
  id: number;
  nickname: string;
  title: string;
  body: string;
  paid_price: number | null;
  price_feeling: PriceFeeling | null;
  rating: number | null;
  created_at: string;
  updated_at: string;
  store: Store | null;
};

export type ReviewPage = { items: Review[]; total: number; page: number; size: number };

/** Either an existing store id or a new store — never both (backend rejects that). */
export type StoreRef = { store_id: number } | { store: NewStore };

export type ReviewFields = {
  nickname: string | null;
  title: string;
  body: string;
  paid_price: number | null;
  price_feeling: PriceFeeling | null;
  rating: number | null;
};

// Backend limits (ReviewCreate / Password in reviews.py)
export const LIMITS = { nickname: 30, title: 100, body: 5000, passwordMin: 4, passwordMaxBytes: 72 };

/** bcrypt only uses 72 bytes, and Korean characters take 3 bytes each in UTF-8. */
export function passwordError(password: string): "short" | "long" | null {
  if (password.length < LIMITS.passwordMin) return "short";
  if (new TextEncoder().encode(password).length > LIMITS.passwordMaxBytes) return "long";
  return null;
}

const json = (body: unknown) => JSON.stringify(body);

export function listReviews(params: { q?: string; page?: number; size?: number }) {
  const qs = new URLSearchParams();
  if (params.q) qs.set("q", params.q);
  if (params.page) qs.set("page", String(params.page));
  if (params.size) qs.set("size", String(params.size));
  return api<ReviewPage>(`/api/reviews?${qs}`);
}

export const getReview = (id: number) => api<Review>(`/api/reviews/${id}`);

export const createReview = (fields: ReviewFields & StoreRef & { password: string }) =>
  api<Review>("/api/reviews", { method: "POST", body: json(fields) });

export const verifyReviewPassword = (id: number, password: string) =>
  api<{ ok: true }>(`/api/reviews/${id}/verify`, { method: "POST", body: json({ password }) });

export const updateReview = (id: number, fields: Partial<ReviewFields> & Partial<StoreRef> & { password: string }) =>
  api<Review>(`/api/reviews/${id}`, { method: "PATCH", body: json(fields) });

export const deleteReview = (id: number, password: string) =>
  api<void>(`/api/reviews/${id}`, { method: "DELETE", body: json({ password }) });

export function searchStores(q: string, limit = 8) {
  const qs = new URLSearchParams({ q, limit: String(limit) });
  return api<Store[]>(`/api/stores?${qs}`);
}

export const formatKrw = (n: number) => `₩${n.toLocaleString("ko-KR")}`;
export const formatDate = (iso: string) =>
  new Date(iso).toLocaleDateString("ko-KR", { year: "numeric", month: "short", day: "numeric" });
