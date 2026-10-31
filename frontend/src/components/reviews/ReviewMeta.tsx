"use client";

import type { PriceFeeling, Store, StoreCategory } from "@/lib/reviews";
import { useDistrictName, useT } from "@/lib/i18n";

// 리뷰에 사진이 없어서, 홈 리뷰 목록 왼쪽 썸네일 자리에 가게 종류 그림을 둔다.
const categoryIcon: Record<StoreCategory, string> = {
  restaurant: "🍽️",
  cafe: "☕",
  bar: "🍺",
  convenience: "🏪",
  market: "🛒",
  shop: "🛍️",
  other: "📍",
};

export function CategoryTile({ category }: { category: StoreCategory | undefined }) {
  return (
    <span aria-hidden className="grid h-14 w-14 shrink-0 place-items-center rounded-2xl bg-brand-soft text-2xl">
      {categoryIcon[category ?? "other"] ?? categoryIcon.other}
    </span>
  );
}

const feelingStyle: Record<PriceFeeling, string> = {
  cheap: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  fair: "bg-slate-50 text-slate-700 ring-slate-200",
  expensive: "bg-rose-50 text-rose-700 ring-rose-200",
};

export function PriceFeelingBadge({ feeling }: { feeling: PriceFeeling }) {
  const t = useT();
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ring-1 ${feelingStyle[feeling]}`}>
      {t.priceFeeling[feeling]}
    </span>
  );
}

export function Stars({ rating }: { rating: number }) {
  const t = useT();
  return (
    <span className="text-amber-500" aria-label={`${t.review.rating} ${rating}/5`}>
      {"★".repeat(rating)}
      <span className="text-slate-300">{"★".repeat(5 - rating)}</span>
    </span>
  );
}

export function StoreTag({ store }: { store: Store }) {
  const t = useT();
  const dn = useDistrictName();
  return (
    <span className="inline-flex items-center gap-1 text-sm text-slate-600">
      <span aria-hidden>📍</span>
      <span className="font-medium text-slate-800">{store.name}</span>
      <span className="text-slate-400">·</span>
      {t.storeCategory[store.category] ?? store.category}
      {store.district && (
        <>
          <span className="text-slate-400">·</span>
          {dn(store.district)}
        </>
      )}
    </span>
  );
}
