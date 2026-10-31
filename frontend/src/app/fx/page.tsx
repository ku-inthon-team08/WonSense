"use client";

import { PageShell } from "@/components/PageShell";
import { FxRates } from "@/components/fx/FxRates";
import { useT } from "@/lib/i18n";
import { card } from "@/lib/ui";

export default function FxPage() {
  const t = useT();
  return (
    <PageShell title={t.fx.title} description={t.fx.pageDesc}>
      <section className={card}>
        <FxRates hideTitle />
      </section>
    </PageShell>
  );
}
