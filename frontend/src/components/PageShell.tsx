import type { ReactNode } from "react";
import { BackChevron } from "@/components/BackChevron";
import { SiteHeader } from "@/components/SiteHeader";
import { frame } from "@/lib/ui";

type Props = {
  title?: string;
  description?: string;
  /** Right side of the title row, e.g. a "write review" button. */
  action?: ReactNode;
  /** Small link above the title, e.g. "← 목록으로". */
  back?: ReactNode;
  /** Where the "<" before the title goes. Home unless the page sits under another (e.g. review form → list). */
  upHref?: string;
  children: ReactNode;
};

// Common frame for every detail page: slim top band + title block + body, same side margins as home.
export function PageShell({ title, description, action, back, upHref = "/", children }: Props) {
  return (
    <>
      <SiteHeader />
      <main className={`${frame} flex-1 py-8 md:py-10`}>
        {back && <div className="mb-3 text-sm text-brand-ink">{back}</div>}
        {title && (
          <div className="mb-6 flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-1">
                <BackChevron href={upHref} />
                <h1 className="text-2xl font-bold">{title}</h1>
              </div>
              {description && <p className="mt-2 text-base text-slate-600">{description}</p>}
            </div>
            {action}
          </div>
        )}
        {children}
      </main>
    </>
  );
}
