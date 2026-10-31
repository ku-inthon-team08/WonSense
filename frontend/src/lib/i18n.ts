"use client";

import { useSyncExternalStore } from "react";

import { SEOUL_DISTRICTS } from "@/lib/seoulDistricts";
import { strings, type Locale, type Strings } from "@/lib/strings";

// The language choice lives in the browser (localStorage), not a cookie: reading cookies on the server would
// force every page out of the prerendered shell under cacheComponents. The server always renders Korean;
// the client switches right after hydration.
const STORAGE_KEY = "wonsense:lang";
const listeners = new Set<() => void>();

/** Saved choice, else the browser language (Korean browsers → ko, everything else → en). */
export function currentLocale(): Locale {
  if (typeof window === "undefined") return "ko";
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "ko" || saved === "en") return saved;
  } catch {
    // private mode / blocked storage: fall through to the browser language
  }
  return navigator.language.toLowerCase().startsWith("ko") ? "ko" : "en";
}

export function setLocale(locale: Locale) {
  try {
    localStorage.setItem(STORAGE_KEY, locale);
  } catch {
    // still switch for this page view
  }
  document.documentElement.lang = locale;
  listeners.forEach((notify) => notify());
}

function subscribe(notify: () => void) {
  listeners.add(notify);
  window.addEventListener("storage", notify); // other tabs
  return () => {
    listeners.delete(notify);
    window.removeEventListener("storage", notify);
  };
}

export function useLocale(): Locale {
  return useSyncExternalStore(subscribe, currentLocale, () => "ko");
}

/** UI strings for the current language. */
export function useT(): Strings {
  return strings[useLocale()];
}

/** Current-language strings outside React (e.g. error messages built in lib/api.ts). */
export const currentStrings = (): Strings => strings[currentLocale()];

const EN_DISTRICT: Record<string, string> = Object.fromEntries(SEOUL_DISTRICTS.map((d) => [d.name, d.nameEn]));

/** District names come from the data in Korean ("마포구"); show "Mapo-gu" in English. */
export function useDistrictName(): (nameKo: string) => string {
  const locale = useLocale();
  return (nameKo) => (locale === "en" ? (EN_DISTRICT[nameKo] ?? nameKo) : nameKo);
}
