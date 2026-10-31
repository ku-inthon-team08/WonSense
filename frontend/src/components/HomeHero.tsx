"use client";

import Image from "next/image";
import Link from "next/link";
import { Nanum_Gothic } from "next/font/google";

import { Logo } from "@/components/Logo";
import { SearchBar } from "@/components/SearchBar";
import { SeoulSkyline } from "@/components/SeoulSkyline";
import { CameraIcon } from "@/components/icons/CameraIcon";
import { ArrowRightIcon } from "@/components/icons/SectionIcons";
import { useT } from "@/lib/i18n";
import { frame } from "@/lib/ui";

const taglineFont = Nanum_Gothic({ weight: "700", subsets: ["latin"] });

// 홈 상단부: 크림색 바탕 + 서울 스카이라인 장식, 왼쪽에 돋보기 든 호랑이, 오른쪽에 로고·검색·스캔.
export function HomeHero() {
  const t = useT();
  return (
    <header className="relative overflow-hidden bg-brand-pale">
      <SeoulSkyline />
      <div className={`${frame} relative flex items-end gap-4 pb-6 pt-5 md:gap-8 md:pb-8 md:pt-7`}>
        <Image
          src="/mascot/horangi-3d-search.webp"
          alt=""
          width={652}
          height={672}
          preload
          className="hidden h-36 w-auto shrink-0 sm:block lg:h-44"
        />
        <div className="min-w-0 flex-1">
          <div className="mb-5 flex flex-wrap items-end gap-x-4 gap-y-1 pr-20 sm:pr-0">
            <h1>
              <Link href="/" aria-label={t.goHome}>
                <Logo label={t.appName} className="h-12 md:h-16" />
              </Link>
            </h1>
            <p className={`${taglineFont.className} translate-y-1 text-base text-slate-600 md:text-xl`}>{t.tagline}</p>
          </div>
          <div className="max-w-4xl">
            <SearchBar />
            <Link
              href="/scan"
              className="mt-3 inline-flex items-center gap-2 rounded-full bg-brand-soft px-4 py-2 text-sm font-medium text-slate-800 ring-1 ring-brand/20 hover:ring-brand/60"
            >
              <CameraIcon className="h-4 w-4 text-brand-ink" />
              {t.scan.entry}
              <ArrowRightIcon className="h-3.5 w-3.5 text-brand-ink" />
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
}
