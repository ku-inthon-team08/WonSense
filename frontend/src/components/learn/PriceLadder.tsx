"use client";

import { useEffect, useState } from "react";

import { GripIcon } from "@/components/icons/SectionIcons";
import { formatKrw } from "@/lib/format";
import { useT } from "@/lib/i18n";
import { RUNGS, byPrice, cardName, cardTip, dealLadder, isSolved, moveRung, type PriceCard } from "@/lib/learn";

// Order four items by price, then see how far apart they really are.
export function PriceLadder({ cards }: { cards: PriceCard[] }) {
  const t = useT();
  const [order, setOrder] = useState(() => dealLadder(cards));
  const [checked, setChecked] = useState(false);
  const [streak, setStreak] = useState(0);
  const [dragKey, setDragKey] = useState<string | null>(null);

  // Listens on window, not the row: the row being dragged moves in the DOM as the order changes.
  useEffect(() => {
    if (!dragKey) return;
    function onMove(e: PointerEvent) {
      const rung = document.elementFromPoint(e.clientX, e.clientY)?.closest<HTMLElement>("[data-rung]");
      if (rung) setOrder((o) => moveRung(o, dragKey!, o.findIndex((c) => c.key === rung.dataset.rung)));
    }
    const stop = () => setDragKey(null);
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", stop);
    window.addEventListener("pointercancel", stop);
    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", stop);
      window.removeEventListener("pointercancel", stop);
    };
  }, [dragKey]);

  function check() {
    setStreak(isSolved(order) ? streak + 1 : 0);
    setChecked(true);
  }

  function next() {
    setOrder(dealLadder(cards));
    setChecked(false);
  }

  return (
    <div className="flex flex-1 flex-col gap-3">
      <p className="text-sm text-slate-600">{t.learn.ladderHint}</p>

      <div className="relative rounded-2xl bg-brand-pale p-4 md:p-5">
        <p className="mb-2 text-center text-xs font-semibold text-brand-ink">▲ {t.learn.ladderTop}</p>
        {checked ? <Answer order={order} /> : <Rungs order={order} dragKey={dragKey} onDrag={setDragKey} onMove={setOrder} />}
        <p className="mt-2 text-center text-xs font-semibold text-brand-ink">▼ {t.learn.ladderBottom}</p>
      </div>

      {checked && <Result order={order} />}

      <div className="mt-auto flex items-center justify-between gap-3 pt-1">
        <span className="text-sm font-medium text-slate-600">{streak > 1 ? t.learn.ladderStreak(streak) : ""}</span>
        {checked ? (
          <button
            type="button"
            onClick={next}
            className="rounded-lg border border-brand px-4 py-2 font-medium text-brand-ink"
          >
            {t.learn.ladderNext} →
          </button>
        ) : (
          <button
            type="button"
            onClick={check}
            className="rounded-lg bg-brand px-5 py-2 font-medium text-slate-900 hover:bg-brand/90"
          >
            {t.learn.ladderCheck}
          </button>
        )}
      </div>
    </div>
  );
}

function Rungs({
  order,
  dragKey,
  onDrag,
  onMove,
}: {
  order: PriceCard[];
  dragKey: string | null;
  onDrag: (key: string) => void;
  onMove: (next: PriceCard[]) => void;
}) {
  const t = useT();
  const arrow = "grid h-8 w-8 shrink-0 place-items-center rounded-lg text-slate-600 hover:bg-brand-pale disabled:text-slate-300";
  return (
    <ul className="relative flex flex-col gap-2">
      {/* The ladder's two rails, showing between the rungs */}
      <span aria-hidden className="absolute inset-y-0 left-6 w-1 rounded-full bg-brand-soft" />
      <span aria-hidden className="absolute inset-y-0 right-6 w-1 rounded-full bg-brand-soft" />
      {order.map((card, i) => {
        const name = cardName(t, card);
        return (
          <li
            key={card.key}
            data-rung={card.key}
            // Mouse drags from anywhere on the rung. Touch only from the grip, so swiping a rung still scrolls the page.
            onPointerDown={(e) => {
              if (e.pointerType === "mouse" && !(e.target as HTMLElement).closest("button")) onDrag(card.key);
            }}
            className={`relative flex h-14 cursor-grab select-none items-center gap-1 rounded-xl bg-white px-2 shadow-card ${
              dragKey === card.key ? "ring-2 ring-brand" : ""
            }`}
          >
            <span onPointerDown={() => onDrag(card.key)} className="grid h-10 w-8 shrink-0 touch-none place-items-center text-slate-400">
              <GripIcon className="h-5 w-5" />
            </span>
            <span className="min-w-0 flex-1 truncate font-medium text-slate-800">{name}</span>
            <button
              type="button"
              aria-label={t.learn.moveUp(name)}
              disabled={i === 0}
              onClick={() => onMove(moveRung(order, card.key, i - 1))}
              className={arrow}
            >
              ↑
            </button>
            <button
              type="button"
              aria-label={t.learn.moveDown(name)}
              disabled={i === order.length - 1}
              onClick={() => onMove(moveRung(order, card.key, i + 1))}
              className={arrow}
            >
              ↓
            </button>
          </li>
        );
      })}
    </ul>
  );
}

// The real order, with bars drawn to scale: the gap between prices is the lesson.
function Answer({ order }: { order: PriceCard[] }) {
  const t = useT();
  const answer = byPrice(order);
  const top = answer[0].price;
  const cheapest = answer[answer.length - 1].price;
  return (
    <ul className="flex flex-col gap-2">
      {answer.map((card, i) => {
        const right = order[i].key === card.key;
        const times = card.price / cheapest;
        return (
          <li key={card.key} className="rounded-xl bg-white p-3 shadow-card">
            <div className="flex items-baseline justify-between gap-2">
              <span className="min-w-0 truncate font-medium text-slate-800">
                <span className={right ? "text-green-700" : "text-rose-600"} aria-label={right ? t.learn.placedRight : t.learn.placedWrong}>
                  {right ? "✓" : "✗"}
                </span>{" "}
                {cardName(t, card)}
              </span>
              <span className="shrink-0 tabular-nums">
                {card.price !== cheapest && (
                  <span className="mr-2 text-xs text-slate-500">×{times >= 10 ? Math.round(times) : times.toFixed(1)}</span>
                )}
                <span className="font-semibold">{formatKrw(card.price)}</span>
              </span>
            </div>
            <div className="mt-2 h-2 rounded-full bg-brand-pale">
              <div className="h-2 rounded-full bg-brand" style={{ width: `${Math.max((card.price / top) * 100, 2)}%` }} />
            </div>
          </li>
        );
      })}
    </ul>
  );
}

function Result({ order }: { order: PriceCard[] }) {
  const t = useT();
  const answer = byPrice(order);
  const solved = isSolved(order);
  const rightCount = answer.filter((card, i) => order[i].key === card.key).length;
  const tipCard = answer.find((card) => cardTip(t, card));
  return (
    <div className={`quiz-pop rounded-lg p-3 ${solved ? "bg-green-100 text-green-900" : "bg-rose-100 text-rose-900"}`} role="status">
      <p className="font-bold">{solved ? t.learn.ladderAllRight : t.learn.ladderSomeRight(rightCount, RUNGS)}</p>
      {tipCard && (
        <p className="mt-1 text-sm">
          {cardName(t, tipCard)}: {cardTip(t, tipCard)}
        </p>
      )}
    </div>
  );
}
