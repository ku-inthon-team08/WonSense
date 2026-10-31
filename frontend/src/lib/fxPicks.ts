"use client";

import { useSyncExternalStore } from "react";

// Which currencies the home exchange-rate card shows. Kept in the browser like the language choice.
const STORAGE_KEY = "wonsense:fx-picks";
export const DEFAULT_PICKS = ["USD", "JPY", "CNY", "EUR"];
export const MAX_PICKS = 4;
const listeners = new Set<() => void>();

let cached: { raw: string | null; picks: string[] } = { raw: null, picks: DEFAULT_PICKS };

function read(): string[] {
  let raw: string | null = null;
  try {
    raw = localStorage.getItem(STORAGE_KEY);
  } catch {
    // blocked storage: defaults
  }
  // Same array while the stored value is unchanged, as useSyncExternalStore requires.
  if (raw !== cached.raw) {
    let picks = DEFAULT_PICKS;
    try {
      const parsed = raw ? JSON.parse(raw) : null;
      if (Array.isArray(parsed) && parsed.length > 0) picks = parsed.filter((c) => typeof c === "string").slice(0, MAX_PICKS);
    } catch {
      // corrupted value: defaults
    }
    cached = { raw, picks };
  }
  return cached.picks;
}

function subscribe(notify: () => void) {
  listeners.add(notify);
  window.addEventListener("storage", notify);
  return () => {
    listeners.delete(notify);
    window.removeEventListener("storage", notify);
  };
}

export function useFxPicks(): string[] {
  return useSyncExternalStore(subscribe, read, () => DEFAULT_PICKS);
}

/** Toggle a currency. At the limit, picking a new one drops the oldest pick; the last one can't be removed. */
export function toggleFxPick(code: string) {
  const picks = read();
  const next = picks.includes(code)
    ? picks.length > 1
      ? picks.filter((c) => c !== code)
      : picks
    : [...picks, code].slice(-MAX_PICKS);
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  } catch {
    return;
  }
  listeners.forEach((notify) => notify());
}
