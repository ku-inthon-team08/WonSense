// GET /api/fx (backend/app/routers/fx.py): KRW per unit of each currency, latest last.
import { api } from "@/lib/api";

export type FxPoint = { date: string; krw: number };

export type FxCurrency = {
  code: string; // USD, JPY, CNY, EUR on home; ~20 more on /fx (all=true)
  unit: number; // JPY, VND, IDR, MNT, UZS are quoted per 100
  krw: number;
  date: string;
  change_pct: number | null; // vs the previous day
  history: FxPoint[];
};

export type FxData = { base: "KRW"; date: string; source: string; currencies: FxCurrency[] };

/** `all` asks for every currency (the /fx page); otherwise just the four shown on home. */
export const fetchFx = (signal?: AbortSignal, all = false) =>
  api<FxData>(all ? "/api/fx?all=true" : "/api/fx", { signal });

// Symbol shown in the round badge. CNY uses 元 so it doesn't look like the yen.
export const FX_SYMBOL: Record<string, string> = {
  USD: "$", JPY: "¥", CNY: "元", EUR: "€", GBP: "£", AUD: "A$", CAD: "C$", NZD: "NZ$", CHF: "Fr",
  HKD: "HK$", TWD: "NT$", SGD: "S$", THB: "฿", VND: "₫", PHP: "₱", IDR: "Rp", MYR: "RM", INR: "₹",
  MNT: "₮", RUB: "₽", KZT: "₸", UZS: "сўм",
};

/** A won amount in another currency: "7.49 USD", "1,180 JPY". Uses the code because ¥ could be yen or yuan. */
export function formatFromKrw(won: number, c: FxCurrency): string {
  const digits = c.code === "JPY" ? 0 : 2;
  const value = (won / c.krw) * c.unit;
  return `${value.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits })} ${c.code}`;
}

/** ₩1,336 for big rates, ₩200.7 when a decimal still matters. */
export const formatFxKrw = (n: number) =>
  `₩${n.toLocaleString("ko-KR", { maximumFractionDigits: n >= 1000 ? 0 : 1, minimumFractionDigits: n >= 1000 ? 0 : 1 })}`;
