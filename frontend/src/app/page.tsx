"use client";

import Image from "next/image";
import Link from "next/link";
import { SearchBar } from "@/components/SearchBar";
import { CameraIcon } from "@/components/icons/CameraIcon";
import { HeatmapPreview } from "@/components/heatmap/HeatmapPreview";
import { SectionHeader } from "@/components/SectionHeader";
import { QuizCard } from "@/components/quiz/QuizCard";
import { LatestReviews } from "@/components/reviews/LatestReviews";
import { useT } from "@/lib/i18n";
import { Nanum_Gothic } from "next/font/google";

const taglineFont = Nanum_Gothic({ weight: "700", subsets: ["latin"] });

// Shared horizontal frame so the top band and the cards line up.
const frame = "mx-auto w-full max-w-[1600px] px-4 md:px-10";
const card = "flex flex-col rounded-2xl bg-white p-5 shadow-card";

export default function Home() {
  const t = useT();
  return (
    <main className="flex flex-1 flex-col">
      {/* Top band: logo + tagline + ① Search */}
      <header className="bg-brand">
        <div className={`${frame} pb-8 pt-5 md:pt-7`}>
          <div className="mb-6 flex flex-wrap items-end gap-x-4 gap-y-2">
            <h1>
              <Image src="/logo_hand_white.png" alt={t.appName} width={886} height={320} preload className="h-14 w-auto md:h-16" />
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
        {/* ② Today's quiz (LLM) */}
        <section className={card}>
          <SectionHeader title={t.quizTitle} href="/quiz" />
          <QuizCard />
        </section>

        <div className="flex flex-col gap-6">
          {/* ③ Heat map (public stats) */}
          <section className={`${card} flex-1`}>
            <SectionHeader title={t.heatmapTitle} href="/heatmap" />
            <HeatmapPreview />
            <p className="mt-auto pt-2 text-xs text-slate-500">{t.heatmapSource}</p>
          </section>

          {/* ④ Reviews (own build) */}
          <section className={`${card} flex-1`}>
            <SectionHeader title={t.reviewTitle} href="/reviews" />
            <LatestReviews />
          </section>
        </div>
      </div>
    </main>
  );
}
