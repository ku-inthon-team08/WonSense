"use client";

import { useEffect } from "react";

import { setLocale, useLocale, useT } from "@/lib/i18n";

// Floating KO/EN switch shown on every page (rendered from the root layout).
export function LanguageToggle() {
  const locale = useLocale();
  const t = useT();

  // The server always renders lang="ko"; keep <html lang> in step with the language actually shown.
  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  return (
    <button
      type="button"
      onClick={() => setLocale(locale === "ko" ? "en" : "ko")}
      aria-label={t.languageToggleLabel}
      className="fixed right-4 top-4 z-50 rounded-full bg-white px-3 py-1.5 text-sm font-medium text-brand shadow-card hover:ring-1 hover:ring-brand/50"
    >
      {t.languageToggle}
    </button>
  );
}
