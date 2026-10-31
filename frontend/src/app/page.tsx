import Image from "next/image";
import Link from "next/link";
import { SearchBar } from "@/components/SearchBar";
import { CameraIcon } from "@/components/icons/CameraIcon";
import { HeatmapPreview } from "@/components/heatmap/HeatmapPreview";
import { SectionHeader } from "@/components/SectionHeader";
import { QuizCard } from "@/components/quiz/QuizCard";
import { LatestReviews } from "@/components/reviews/LatestReviews";
import { t } from "@/lib/strings";
import { card, frame } from "@/lib/ui";
import { Nanum_Gothic } from "next/font/google";

const taglineFont = Nanum_Gothic({ weight: "700", subsets: ["latin"] });

export default function Home() {
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
          {/* Search + scan share one row; the button stretches to the search bar's height. */}
          <div className="flex gap-3">
            <div className="min-w-0 flex-1">
              <SearchBar />
            </div>
            <Link
              href="/scan"
              aria-label={t.scan.entry}
              className="inline-flex shrink-0 items-center gap-2 rounded-full bg-white/20 px-4 text-sm font-medium text-white hover:bg-white/30 md:px-5"
            >
              <CameraIcon className="h-5 w-5" />
              <span className="hidden md:inline">{t.scan.entry}</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Cards fill the rest of the viewport on md+ */}
      <div className={`${frame} grid flex-1 gap-6 py-6 md:grid-cols-2 md:py-8`}>
        {/* ② Today's quiz (LLM) */}
        <section className={card}>
          <SectionHeader title={t.quizTitle} href="/quiz" />
          <QuizCard />
        </section>

        {/* Two equal rows: the review card is always as tall as the heat map card. */}
        <div className="grid auto-rows-fr gap-6">
          {/* ③ Heat map (public stats) */}
          <section className={card}>
            <SectionHeader title={t.heatmapPageTitle} href="/heatmap" />
            <HeatmapPreview />
            <p className="mt-auto pt-2 text-xs text-slate-500">{t.heatmapSource}</p>
          </section>

          {/* ④ Reviews (own build) — list is taken out of flow so it never grows the card; overflow fades to white. */}
          <section className={card}>
            <SectionHeader title={t.review.pageTitle} href="/reviews" />
            <div className="relative min-h-40 flex-1">
              {/* -inset-x-1 + px-1/pt-1 leave room so the review cards' shadows aren't clipped. */}
              <div className="absolute -inset-x-1 inset-y-0 overflow-hidden px-1 pt-1">
                <LatestReviews />
              </div>
              <div aria-hidden className="pointer-events-none absolute inset-x-0 bottom-0 h-16 bg-linear-to-t from-white to-transparent" />
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
