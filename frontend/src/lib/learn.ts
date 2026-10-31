// GET /api/quiz/prices (backend/app/routers/quiz.py): the price cards behind the Budget Quiz and Price Ladder.
// One request loads them all, so new questions and rounds never call the API.
import { api } from "@/lib/api";
import type { Strings } from "@/lib/strings";

export type PriceCard = {
  key: string;
  kind: "grocery" | "dish";
  name: string;
  name_en: string | null;
  price: number; // grocery: Seoul average, dish: median at good-price restaurants
  anchor: boolean; // familiar item, shown as "how many can you buy"
  tip: string | null;
  tip_en: string | null;
};

export type PriceCards = { cards: PriceCard[]; reference_date: string | null };

export const fetchPriceCards = (signal?: AbortSignal) => api<PriceCards>("/api/quiz/prices", { signal });

export const cardName = (t: Strings, card: PriceCard) => (t.lang === "en" && card.name_en ? card.name_en : card.name);
export const cardTip = (t: Strings, card: PriceCard) => (t.lang === "en" ? card.tip_en : card.tip);

function shuffled<T>(list: T[]): T[] {
  const out = [...list];
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

// "Odae rice, 4kg" and "Odae rice, 10kg" are one family: comparing them teaches nothing.
const familyOf = (card: PriceCard) => (card.name_en ?? card.name).split(",")[0];

/** Every familiar item, cheapest first, with how many this amount buys (0 when it can't). */
export function familiarBuys(cards: PriceCard[], won: number) {
  return cards
    .filter((c) => c.anchor)
    .sort((a, b) => a.price - b.price)
    .map((card) => ({ card, count: Math.floor(won / card.price) }));
}

// ₩50,000 is left out: only two kinds of item cost more, so it can't fill the wrong answers.
const BUDGETS = [3000, 5000, 10000, 15000, 20000, 30000];
const OPTIONS = 4;
// Prices are averages, so the right answer has to leave real change and the wrong ones have to be clearly too
// dear: ₩9,900 against a ₩10,000 budget would be a coin flip.
const FITS = { min: 0.5, max: 0.9 };
const TOO_DEAR = { min: 1.2, max: 3 };

export type BudgetQuestion = { budget: number; answer: PriceCard; options: PriceCard[] };

const pricedWithin = (cards: PriceCard[], budget: number, { min, max }: { min: number; max: number }) =>
  cards.filter((c) => c.price >= budget * min && c.price <= budget * max);

/** One card that fits the budget and three that don't, so exactly one answer is right. */
export function dealBudgetQuestion(cards: PriceCard[], lastBudget?: number): BudgetQuestion | null {
  for (const budget of shuffled(BUDGETS.filter((b) => b !== lastBudget))) {
    const answer = shuffled(pricedWithin(cards, budget, FITS))[0];
    if (!answer) continue;
    const options = [answer];
    for (const card of shuffled(pricedWithin(cards, budget, TOO_DEAR))) {
      if (options.every((o) => familyOf(o) !== familyOf(card))) options.push(card);
      if (options.length === OPTIONS) return { budget, answer, options: shuffled(options) };
    }
  }
  return null;
}

export const RUNGS = 4;
const MIN_RATIO = 1.3; // prices closer than this are a coin flip

const canTellApart = (a: PriceCard, b: PriceCard) =>
  familyOf(a) !== familyOf(b) && Math.max(a.price, b.price) / Math.min(a.price, b.price) >= MIN_RATIO;

/** The priciest card goes on top of the ladder. */
export const isSolved = (order: PriceCard[]) => order.every((c, i) => i === 0 || order[i - 1].price >= c.price);

export const byPrice = (cards: PriceCard[]) => [...cards].sort((a, b) => b.price - a.price);

/** Four cards priced far enough apart to tell them apart, in an order that isn't already solved. */
export function dealLadder(cards: PriceCard[]): PriceCard[] {
  for (let attempt = 0; attempt < 20; attempt++) {
    const hand: PriceCard[] = [];
    for (const card of shuffled(cards)) {
      if (hand.every((h) => canTellApart(h, card))) hand.push(card);
      if (hand.length === RUNGS) break;
    }
    if (hand.length === RUNGS && !isSolved(hand)) return hand;
  }
  return shuffled(cards).slice(0, RUNGS);
}

/** The order after moving `key` to the rung at index `to`. */
export function moveRung(order: PriceCard[], key: string, to: number): PriceCard[] {
  const card = order.find((c) => c.key === key);
  if (!card || to < 0 || to >= order.length) return order;
  const rest = order.filter((c) => c.key !== key);
  return [...rest.slice(0, to), card, ...rest.slice(to)];
}
