"use client";

import Link from "next/link";
import { Logo } from "@/components/Logo";
import { useT } from "@/lib/i18n";
import { frame } from "@/lib/ui";

// Slim version of the home top band for detail pages. The logo always links home.
export function SiteHeader() {
  const t = useT();
  return (
    <header className="border-b border-brand/15 bg-brand-pale">
      <div className={`${frame} py-3 md:py-4`}>
        <Link href="/" aria-label={t.goHome} className="inline-block">
          <Logo label="" className="h-9 md:h-10" />
        </Link>
      </div>
    </header>
  );
}
