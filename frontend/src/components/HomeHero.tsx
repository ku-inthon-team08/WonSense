"use client";

import Image from "next/image";
import Link from "next/link";
import { Nanum_Gothic } from "next/font/google";

import { Logo } from "@/components/Logo";
import { SearchBar } from "@/components/SearchBar";
import { CameraIcon } from "@/components/icons/CameraIcon";
import { ArrowRightIcon } from "@/components/icons/SectionIcons";
import { useT } from "@/lib/i18n";
import { frame } from "@/lib/ui";

const taglineFont = Nanum_Gothic({ weight: "700", subsets: ["latin"] });

// 홈 상단부: 서울 스카이라인 배경 그림(public/hero-bg.webp) 위에
// 왼쪽 = 로고 + 그 밑 돋보기 든 호랑이, 오른쪽 = 태그라인 + 검색창 + (검색창 오른편) 바가지 확인 버튼.
export function HomeHero() {
  const t = useT();
  return (
    <header className="bg-brand-pale bg-[url(/hero-bg.webp)] bg-cover bg-bottom">
      <div className={`${frame} grid items-center gap-x-10 gap-y-4 pb-8 pt-5 sm:grid-cols-[auto_minmax(0,1fr)] md:pb-12 md:pt-7`}>
        <div className="flex flex-col items-start pr-20 sm:pr-0">
          <h1>
            <Link href="/" aria-label={t.goHome}>
              <Logo label={t.appName} className="h-12 md:h-16" />
            </Link>
          </h1>
          <Image
            src="/mascot/horangi-3d-search.webp"
            alt=""
            width={652}
            height={672}
            preload
            className="mt-3 hidden h-32 w-auto sm:block lg:h-40"
          />
        </div>

        <div className="min-w-0 max-w-5xl">
          <p className={`${taglineFont.className} mb-4 text-base text-slate-600 md:text-xl`}>{t.tagline}</p>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <div className="min-w-0 flex-1">
              <SearchBar />
            </div>
            <Link
              href="/scan"
              className="inline-flex h-14 shrink-0 items-center justify-center gap-2 rounded-full bg-brand-soft px-5 text-sm font-medium text-slate-800 shadow-card ring-1 ring-brand/20 hover:ring-brand/60"
            >
              <CameraIcon className="h-5 w-5 text-brand-ink" />
              {t.scan.entry}
              <ArrowRightIcon className="h-3.5 w-3.5 text-brand-ink" />
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
}
