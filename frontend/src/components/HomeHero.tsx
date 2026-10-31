"use client";

import Image from "next/image";
import Link from "next/link";
import type { CSSProperties } from "react";

import { Logo } from "@/components/Logo";
import { SearchBar } from "@/components/SearchBar";
import { CameraIcon } from "@/components/icons/CameraIcon";
import { ArrowRightIcon, ChartIcon, QuizIcon, StarIcon } from "@/components/icons/SectionIcons";
import { useT } from "@/lib/i18n";
import { frame } from "@/lib/ui";

// 홈 첫 화면(한 화면 꽉): 서울 스카이라인 배경 위에
// 맨 위 = 작은 로고, 왼쪽 = 태그라인 칩 + 질문형 헤드라인 + 핵심 기능(① 가격표 스캔 | ② 검색) + 나머지 기능 바로가기,
// 오른쪽 = 돋보기 든 호랑이(바닥 그림자, 좁은 화면에서는 헤드라인 아래). 아래로 스크롤하면 카드 화면으로 넘어간다.
export function HomeHero() {
  const t = useT();
  const shortcuts = [
    { href: "/quiz", label: t.quizTitle, Icon: QuizIcon },
    { href: "/heatmap", label: t.heatmapPageTitle, Icon: ChartIcon },
    { href: "/reviews", label: t.review.pageTitle, Icon: StarIcon },
  ];

  return (
    <header className="hero relative flex min-h-svh snap-start flex-col overflow-hidden bg-brand-pale bg-[url(/hero-bg.webp)] bg-cover bg-bottom">
      {/* Top bar: small logo on the left; the language toggle (fixed, from layout) sits opposite. */}
      <div className={`${frame} hero-rise pt-4`}>
        <h1 className="flex h-9 items-center">
          <Link href="/" aria-label={t.goHome}>
            <Logo label={t.appName} className="h-7 md:h-8" />
          </Link>
        </h1>
      </div>

      <div className={`${frame} grid flex-1 items-center gap-6 pb-24 pt-4 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)] lg:gap-10`}>
        <div className="hero-content min-w-0 max-w-2xl">
          <div className="hero-rise" style={{ "--rise-delay": "0.06s" } as CSSProperties}>
            <p className="inline-flex items-center gap-1.5 rounded-full bg-brand-soft/80 px-3.5 py-1.5 text-sm font-semibold text-brand-ink">
              <PinIcon className="h-4 w-4" />
              {t.tagline}
            </p>
            <h2 className="mt-5 max-w-[9em] text-balance text-4xl font-extrabold leading-[1.15] tracking-[-0.035em] text-slate-900 md:text-6xl">
              {t.heroTitle}
            </h2>
            <p className="mt-4 text-base font-medium leading-relaxed text-slate-600 md:text-lg">{t.heroIntro}</p>
          </div>

          {/* Below lg the tiger moves out of the right column and sits under the headline. */}
          <HeroStage className="mx-auto mt-6 w-40 sm:w-48 lg:hidden" />

          {/* Core actions side by side: snapping a price tag (primary) and search. */}
          <div className="hero-rise mt-8 flex flex-col gap-3 sm:flex-row sm:items-center" style={{ "--rise-delay": "0.14s" } as CSSProperties}>
            <Link
              href="/scan"
              className="group inline-flex min-h-14 shrink-0 items-center justify-center gap-2.5 rounded-full bg-brand px-6 py-3 text-center text-base font-bold leading-snug text-slate-900 shadow-card transition hover:brightness-95 active:scale-[0.98]"
            >
              <CameraIcon className="h-5 w-5" />
              {t.scan.entry}
              <ArrowRightIcon className="h-3.5 w-3.5 transition-transform group-hover:translate-x-1" />
            </Link>
            <div className="min-w-0 flex-1 sm:max-w-sm">
              <SearchBar placeholder={t.heroSearchPlaceholder} />
            </div>
          </div>

          <div className="hero-rise mt-7" style={{ "--rise-delay": "0.22s" } as CSSProperties}>
            <p className="mb-2.5 text-sm font-medium text-slate-500">{t.heroOr}</p>
            <ul className="flex flex-wrap gap-2">
              {shortcuts.map(({ href, label, Icon }) => (
                <li key={href}>
                  <Link
                    href={href}
                    className="inline-flex items-center gap-1.5 rounded-full bg-white/85 px-3.5 py-2 text-sm font-medium text-slate-700 shadow-card ring-1 ring-brand/10 backdrop-blur hover:bg-white hover:ring-brand/50"
                  >
                    <Icon className="h-4 w-4 text-brand-ink" />
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <HeroStage className="hidden w-full max-w-lg justify-self-center lg:block" />
      </div>

      <a
        href="#home-content"
        className="absolute bottom-6 left-1/2 flex -translate-x-1/2 flex-col items-center gap-1 text-xs font-medium text-slate-500 hover:text-brand-ink"
      >
        {t.scrollCue}
        <span aria-hidden className="scroll-cue-arrow text-base">
          ↓
        </span>
      </a>
    </header>
  );
}

// Tiger standing on a soft floor shadow, with a few "aha" spark lines by the magnifier.
function HeroStage({ className = "" }: { className?: string }) {
  return (
    <div aria-hidden className={`hero-stage pointer-events-none relative aspect-square ${className}`}>
      <div className="absolute bottom-[3%] left-1/2 h-[9%] w-[62%] -translate-x-1/2 rounded-[50%] bg-[radial-gradient(closest-side,rgb(120_84_20/0.28),transparent)]" />
      <Image src="/mascot/horangi-3d-search.webp" alt="" width={652} height={672} preload className="absolute inset-x-[4%] bottom-[6%] h-[90%] w-[92%] object-contain" />
      <svg viewBox="0 0 40 40" className="absolute right-[12%] top-[2%] w-[13%] text-brand" fill="none" stroke="currentColor" strokeWidth={4} strokeLinecap="round">
        <path d="M8 22 6 10M18 18l6-10M24 28l11-4" />
      </svg>
    </div>
  );
}

function PinIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden className={className}>
      <path d="M12 2a7 7 0 0 0-7 7c0 5.2 7 13 7 13s7-7.8 7-13a7 7 0 0 0-7-7Zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5Z" />
    </svg>
  );
}
