import { PageShell } from "@/components/PageShell";
import { ScanView } from "@/components/scan/ScanView";
import { t } from "@/lib/strings";

export default function ScanPage() {
  return (
    <PageShell title={t.scan.pageTitle} description={t.scan.pageDesc}>
      <ScanView />
    </PageShell>
  );
}
