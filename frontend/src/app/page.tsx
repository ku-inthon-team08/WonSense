import Image from "next/image";
import { SearchBar } from "@/components/SearchBar";
import { SectionHeader } from "@/components/SectionHeader";
import { QuizCard } from "@/components/quiz/QuizCard";
import { t } from "@/lib/strings";
import { Nanum_Gothic } from "next/font/google";

const taglineFont = Nanum_Gothic({ weight: "700", subsets: ["latin"] });

// Shared horizontal frame so the top band and the cards line up.
const frame = "mx-auto w-full max-w-[1600px] px-4 md:px-10";
const card = "flex flex-col rounded-2xl bg-white p-5 shadow-card";

export default function Home() {
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
            <div className="relative min-h-32 flex-1 overflow-hidden rounded-xl bg-stone-50">
              <div className="absolute left-[8%] top-1/4 h-24 w-24 rounded-full bg-yellow-200/80 blur-xl" />
              <div className="absolute left-1/3 top-[20%] h-28 w-32 rounded-full bg-brand/60 blur-xl" />
              <div className="absolute right-[8%] top-1/3 h-24 w-24 rounded-full bg-amber-300/60 blur-xl" />
            </div>
            <p className="mt-2 text-xs text-slate-500">{t.heatmapSource}</p>
          </section>

          {/* ④ Reviews (own build) */}
          <section className={`${card} flex-1`}>
            <SectionHeader title={t.reviewTitle} href="/reviews" />
            <div className="flex min-h-24 flex-1 items-center justify-center rounded-xl border border-dashed border-slate-300 p-6 text-sm text-slate-500">
              {t.reviewEmpty}
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
