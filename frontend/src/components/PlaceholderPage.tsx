import Link from "next/link";
import { t } from "@/lib/strings";

// Stand-in for detail pages that aren't built yet.
export function PlaceholderPage({ title }: { title: string }) {
  return (
    <main className="mx-auto w-full max-w-[1600px] flex-1 px-4 py-6 md:px-10">
      <Link href="/" className="text-sm text-brand">{t.backHome}</Link>
      <h1 className="mt-2 text-2xl font-bold">{title}</h1>
      <p className="mt-2 text-slate-500">{t.comingSoon}</p>
    </main>
  );
}
