"use client";

import Image from "next/image";
import Link from "next/link";
import { useT } from "@/lib/i18n";
import { frame } from "@/lib/ui";

// Slim version of the home top band for detail pages. The logo always links home.
export function SiteHeader() {
  const t = useT();
  return (
    <header className="bg-brand">
      <div className={`${frame} py-3 md:py-4`}>
        <Link href="/" aria-label={t.goHome} className="inline-block">
          <Image src="/logo_hand_white.png" alt="" width={886} height={320} preload className="h-9 w-auto md:h-10" />
        </Link>
      </div>
    </header>
  );
}
