"use client";

import { PageShell } from "@/components/PageShell";
import { ScanView } from "@/components/scan/ScanView";
import { useT } from "@/lib/i18n";

export default function ScanPage() {
  const t = useT();
  return (
    <PageShell title={t.scan.pageTitle} description={t.scan.pageDesc}>
      <ScanView />
    </PageShell>
  );
}
