"use client";

import Image from "next/image";
import Link from "next/link";
import { SearchBar } from "@/components/SearchBar";
import { CameraIcon } from "@/components/icons/CameraIcon";
import { HeatmapPreview } from "@/components/heatmap/HeatmapPreview";
import { SectionHeader } from "@/components/SectionHeader";
import { FxRates } from "@/components/fx/FxRates";
import { QuizCard } from "@/components/quiz/QuizCard";
import { LatestReviews } from "@/components/reviews/LatestReviews";
import { useT } from "@/lib/i18n";
import { card, frame } from "@/lib/ui";
import { Nanum_Gothic } from "next/font/google";

const taglineFont = Nanum_Gothic({ weight: "700", subsets: ["latin"] });

export default function Home() {
  const t = useT();
  return (
    <main className="flex flex-1 flex-col">
      {/* Top band: logo + tagline + ① Search */}
      <header className="bg-brand">
        <div className={`${frame} pb-8 pt-5 md:pt-7`}>
          <div className="mb-6 flex flex-wrap items-end gap-x-4 gap-y-2">
            <h1>
              <Link href="/">
                <Image src="/logo_hand_white.png" alt={t.appName} width={886} height={320} preload className="h-14 w-auto md:h-16" />
              </Link>
            </h1>
            <p className={`${taglineFont.className} translate-y-1 text-base text-brand-pale md:text-xl`}>{t.tagline}</p>
          </div>
          <SearchBar />
          <Link
            href="/scan"
            className="mt-3 inline-flex items-center gap-2 rounded-full bg-white/20 px-4 py-2 text-sm font-medium text-white hover:bg-white/30"
          >
            <CameraIcon className="h-5 w-5" />
            {t.scan.entry}
          </Link>
        </div>
      </header>

      {/* Cards fill the rest of the viewport on md+ */}
      <div className={`${frame} grid flex-1 gap-6 py-6 md:grid-cols-2 md:py-8`}>
        {/* ② Price quiz (+ exchange rates) */}
        <section className={card}>
          <SectionHeader title={t.quizTitle} href="/quiz" />
          <QuizCard />
          {/* mt-auto: sits at the bottom of the quiz card, which is as tall as the right column */}
          <div className="mt-auto pt-5">
            <FxRates />
          </div>
        </section>

        <div className="flex flex-col gap-6">
          {/* ③ Heat map (public stats) */}
          <section className={`${card} flex-1`}>
            <SectionHeader title={t.heatmapPageTitle} href="/heatmap" />
            <HeatmapPreview />
            <p className="mt-auto pt-2 text-xs text-slate-500">{t.heatmapSource}</p>
          </section>

          {/* ④ Reviews (own build) */}
          <section className={`${card} flex-1`}>
            <SectionHeader title={t.review.pageTitle} href="/reviews" />
            <LatestReviews />
          </section>
        </div>
      </div>
    </main>
  );
}
