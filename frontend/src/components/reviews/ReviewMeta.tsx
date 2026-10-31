import type { PriceFeeling, Store } from "@/lib/reviews";
import { t } from "@/lib/strings";

const feelingStyle: Record<PriceFeeling, string> = {
  cheap: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  fair: "bg-slate-50 text-slate-700 ring-slate-200",
  expensive: "bg-rose-50 text-rose-700 ring-rose-200",
};

export function PriceFeelingBadge({ feeling }: { feeling: PriceFeeling }) {
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ring-1 ${feelingStyle[feeling]}`}>
      {t.priceFeeling[feeling]}
    </span>
  );
}

export function Stars({ rating }: { rating: number }) {
  return (
    <span className="text-amber-500" aria-label={`${t.review.rating} ${rating}/5`}>
      {"★".repeat(rating)}
      <span className="text-slate-300">{"★".repeat(5 - rating)}</span>
    </span>
  );
}

export function StoreTag({ store }: { store: Store }) {
  return (
    <span className="inline-flex items-center gap-1 text-sm text-slate-600">
      <span aria-hidden>📍</span>
      <span className="font-medium text-slate-800">{store.name}</span>
      <span className="text-slate-400">·</span>
      {t.storeCategory[store.category] ?? store.category}
      {store.district && (
        <>
          <span className="text-slate-400">·</span>
          {store.district}
        </>
      )}
    </span>
  );
}
