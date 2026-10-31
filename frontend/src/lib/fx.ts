// GET /api/fx (backend/app/routers/fx.py): KRW per unit of each currency, latest last.
import { api } from "@/lib/api";

export type FxPoint = { date: string; krw: number };

export type FxCurrency = {
  code: "USD" | "JPY" | "CNY" | "EUR";
  unit: number; // JPY is quoted per 100 yen
  krw: number;
  date: string;
  change_pct: number | null; // vs the previous day
  history: FxPoint[];
};

export type FxData = { base: "KRW"; date: string; source: string; currencies: FxCurrency[] };

export const fetchFx = (signal?: AbortSignal) => api<FxData>("/api/fx", { signal });

// Symbol shown in the round badge. CNY uses 元 so it doesn't look like the yen.
export const FX_SYMBOL: Record<string, string> = { USD: "$", JPY: "¥", CNY: "元", EUR: "€" };

/** ₩1,336 for big rates, ₩200.7 when a decimal still matters. */
export const formatFxKrw = (n: number) =>
  `₩${n.toLocaleString("ko-KR", { maximumFractionDigits: n >= 1000 ? 0 : 1, minimumFractionDigits: n >= 1000 ? 0 : 1 })}`;
