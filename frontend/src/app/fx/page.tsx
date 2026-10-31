"use client";

import { PageShell } from "@/components/PageShell";
import { FxConverter } from "@/components/fx/FxConverter";
import { FxRates } from "@/components/fx/FxRates";
import { useT } from "@/lib/i18n";
import { card } from "@/lib/ui";

export default function FxPage() {
  const t = useT();
  return (
    <PageShell title={t.fx.title} description={t.fx.pageDesc}>
      <div className="flex flex-col gap-6">
        <section className={card}>
          <FxConverter />
        </section>
        <section className={card}>
          <FxRates hideTitle all />
        </section>
      </div>
    </PageShell>
  );
}
