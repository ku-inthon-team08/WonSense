import Link from "next/link";
import type { ReactNode } from "react";

import { ArrowRightIcon } from "@/components/icons/SectionIcons";

type Props = {
  title: string;
  href: string;
  /** 제목 앞 아이콘 (SectionIcons). 없으면 brand 점. */
  icon?: ReactNode;
  /** 오른쪽 끝 알약 링크 문구 (예: "자세히 보기"). 같은 href로 간다. */
  actionLabel?: string;
};

export function SectionHeader({ title, href, icon, actionLabel }: Props) {
  return (
    <div className="mb-4 flex items-center justify-between gap-3">
      <Link href={href} className="group flex items-center gap-2.5 text-lg font-semibold text-slate-900">
        {icon ? (
          <span aria-hidden className="grid h-8 w-8 place-items-center rounded-full bg-brand-soft text-brand-ink">
            {icon}
          </span>
        ) : (
          <span aria-hidden className="h-2.5 w-2.5 rounded-full bg-brand" />
        )}
        {title}
        <ArrowRightIcon className="h-4 w-4 text-brand-ink transition-transform group-hover:translate-x-1" />
      </Link>
      {actionLabel && (
        <Link
          href={href}
          className="hidden shrink-0 items-center gap-1 rounded-full bg-white px-3 py-1.5 text-sm font-medium text-slate-700 ring-1 ring-slate-200 hover:ring-brand/60 sm:inline-flex"
        >
          {actionLabel}
          <ArrowRightIcon className="h-3.5 w-3.5" />
        </Link>
      )}
    </div>
  );
}
