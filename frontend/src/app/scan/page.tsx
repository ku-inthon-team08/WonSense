import Link from "next/link";

import { ScanView } from "@/components/scan/ScanView";
import { t } from "@/lib/strings";

export default function ScanPage() {
  return (
    <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-6">
      <Link href="/" className="text-sm text-brand">{t.home}</Link>
      <h1 className="mt-2 text-2xl font-bold">{t.scan.pageTitle}</h1>
      <p className="mt-1 text-sm text-slate-500">{t.scan.pageDesc}</p>
      <div className="mt-6">
        <ScanView />
      </div>
    </main>
  );
}
