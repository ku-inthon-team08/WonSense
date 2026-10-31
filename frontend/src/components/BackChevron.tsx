"use client";

import Link from "next/link";

import { useT } from "@/lib/i18n";

// "<" in front of a detail page title. Goes home by default, or one level up (e.g. review form → list).
export function BackChevron({ href = "/" }: { href?: string }) {
  const t = useT();
  return (
    <Link
      href={href}
      aria-label={href === "/" ? t.goHome : t.back}
      className="-ml-2 grid h-10 w-10 shrink-0 place-items-center rounded-full text-slate-900 transition hover:bg-brand-soft active:scale-95"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden className="h-6 w-6">
        <path d="M15 5l-7 7 7 7" />
      </svg>
    </Link>
  );
}
