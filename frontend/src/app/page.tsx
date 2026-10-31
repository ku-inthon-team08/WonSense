import { SearchBar } from "@/components/SearchBar";
import { HeatmapPreview } from "@/components/heatmap/HeatmapPreview";
import { SectionHeader } from "@/components/SectionHeader";
import { QuizCard } from "@/components/quiz/QuizCard";
import { t } from "@/lib/strings";

export default function Home() {
  return (
    <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-6">
      <header className="mb-4 flex items-baseline gap-2">
        <h1 className="text-2xl font-bold text-indigo-700">{t.appName}</h1>
        <span className="text-sm text-slate-500">{t.tagline}</span>
      </header>

      {/* ① Search */}
      <section className="mb-6">
        <SearchBar />
      </section>

      <div className="grid gap-6 md:grid-cols-2">
        {/* ② Today's quiz (LLM) */}
        <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <SectionHeader num={2} title={t.quizTitle} href="/quiz" />
          <QuizCard />
        </section>

        <div className="flex flex-col gap-6">
          {/* ③ Heat map (public stats) */}
          <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <SectionHeader num={3} title={t.heatmapTitle} href="/heatmap" />
            <HeatmapPreview />
            <p className="mt-2 text-xs text-slate-500">{t.heatmapSource}</p>
          </section>

          {/* ④ Reviews (own build) */}
          <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <SectionHeader num={4} title={t.reviewTitle} href="/reviews" />
            <div className="rounded-xl border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">
              {t.reviewEmpty}
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
