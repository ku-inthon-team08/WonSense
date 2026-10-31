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
      {/* 첫 화면: 로고 + 헤드라인 + ① 스캔·검색 + 바로가기 + 호랑이 */}
      <HomeHero />

      {/* 2×2 카드: 퀴즈 | 지도 / 환율 | 리뷰 */}
      <div id="home-content" className={`${frame} grid flex-1 snap-start gap-6 py-6 md:grid-cols-2 md:py-8`}>
        {/* ② 물가 퀴즈 */}
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
          />
          <HeatmapPreview />
          <p className="mt-auto pt-3 text-xs text-slate-500">{t.heatmapSource}</p>
        </section>

        {/* 오늘의 환율 */}
        <section className={card}>
          <FxRates href="/fx" />
        </section>

        {/* ④ 리뷰 (자체 개발) */}
        <section className={card}>
          <SectionHeader
            title={t.review.pageTitle}
            href="/reviews"
            icon={<StarIcon className="h-4 w-4" />}
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
