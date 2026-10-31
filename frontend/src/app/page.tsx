"use client";

import { HomeHero } from "@/components/HomeHero";
import { HeatmapPreview } from "@/components/heatmap/HeatmapPreview";
import { SectionHeader } from "@/components/SectionHeader";
import { FxRates } from "@/components/fx/FxRates";
import { ChartIcon, QuizIcon, StarIcon } from "@/components/icons/SectionIcons";
import { QuizCard } from "@/components/quiz/QuizCard";
import { LatestReviews } from "@/components/reviews/LatestReviews";
import { useT } from "@/lib/i18n";
import { card, frame } from "@/lib/ui";

export default function Home() {
  const t = useT();
  return (
    <main className="flex flex-1 flex-col">
      {/* 상단부: 호랑이 + 로고 + 태그라인 + ① 검색 + 스캔 */}
      <HomeHero />

      {/* 2×2 카드: 퀴즈 | 지도 / 환율 | 리뷰 */}
      <div className={`${frame} grid flex-1 gap-6 py-6 md:grid-cols-2 md:py-8`}>
        {/* ② 물가 퀴즈 (LLM) */}
        <section className={card}>
          <SectionHeader title={t.quizTitle} href="/quiz" icon={<QuizIcon className="h-4 w-4" />} />
          <QuizCard mascot />
        </section>

        {/* ③ 히트맵 (공공 통계) */}
        <section className={card}>
          <SectionHeader
            title={t.heatmapPageTitle}
            href="/heatmap"
            icon={<ChartIcon className="h-4 w-4" />}
            actionLabel={t.viewDetails}
          />
          <HeatmapPreview />
          <p className="mt-auto pt-3 text-xs text-slate-500">{t.heatmapSource}</p>
        </section>

        {/* 오늘의 환율 */}
        <section className={card}>
          <FxRates />
        </section>

        {/* ④ 리뷰 (자체 개발) */}
        <section className={card}>
          <SectionHeader
            title={t.review.pageTitle}
            href="/reviews"
            icon={<StarIcon className="h-4 w-4" />}
            actionLabel={t.seeMore}
          />
          {/* On md+ the list is taken out of flow so the card stays as tall as its row neighbour; overflow fades to white. */}
          <div className="relative flex-1 md:min-h-40">
            <div className="md:absolute md:inset-0 md:overflow-hidden">
              <LatestReviews />
            </div>
            <div aria-hidden className="pointer-events-none absolute inset-x-0 hidden md:block bottom-0 h-16 bg-linear-to-t from-white to-transparent" />
          </div>
        </section>
      </div>
    </main>
  );
}
