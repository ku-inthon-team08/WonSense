import type { CSSProperties } from "react";

// Loading placeholders (see .skeleton in globals.css). Screen readers hear `label` once instead of empty boxes.

/** One shimmering block; size and shape come from className. `i` staggers the wave between neighbours. */
export function Skeleton({ className = "", i = 0 }: { className?: string; i?: number }) {
  return <div aria-hidden className={`skeleton ${className}`} style={{ "--i": i } as CSSProperties} />;
}

/** Wrapper that announces loading once. */
export function SkeletonGroup({ label, className = "", children }: { label: string; className?: string; children: React.ReactNode }) {
  return (
    <div role="status" aria-live="polite" className={className}>
      <span className="sr-only">{label}</span>
      {children}
    </div>
  );
}

/** List rows: a square thumbnail and two text lines, like review rows and search cards. */
export function SkeletonRows({ label, rows = 3, className = "" }: { label: string; rows?: number; className?: string }) {
  return (
    <SkeletonGroup label={label} className={`flex flex-col gap-4 ${className}`}>
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="flex items-center gap-3">
          <Skeleton i={i} className="h-12 w-12 shrink-0 rounded-xl" />
          <div className="flex flex-1 flex-col gap-2">
            <Skeleton i={i} className="h-4 w-2/5 rounded-full" />
            <Skeleton i={i + 0.5} className="h-3.5 w-4/5 rounded-full" />
          </div>
        </div>
      ))}
    </SkeletonGroup>
  );
}

/** Big cards (search results, detail pages). */
export function SkeletonCards({ label, cards = 3, className = "" }: { label: string; cards?: number; className?: string }) {
  return (
    <SkeletonGroup label={label} className={`flex flex-col gap-4 ${className}`}>
      {Array.from({ length: cards }, (_, i) => (
        <div key={i} className="flex flex-col gap-3 rounded-2xl bg-white p-5 ring-1 ring-slate-100">
          <Skeleton i={i} className="h-5 w-1/3 rounded-full" />
          <Skeleton i={i + 0.3} className="h-8 w-1/2 rounded-lg" />
          <Skeleton i={i + 0.6} className="h-3 w-full rounded-full" />
          <Skeleton i={i + 0.9} className="h-3 w-3/4 rounded-full" />
        </div>
      ))}
    </SkeletonGroup>
  );
}

/** A few text lines of varying width. */
export function SkeletonLines({ label, lines = 3, className = "" }: { label: string; lines?: number; className?: string }) {
  const widths = ["w-full", "w-5/6", "w-2/3", "w-3/4"];
  return (
    <SkeletonGroup label={label} className={`flex flex-col gap-2.5 ${className}`}>
      {Array.from({ length: lines }, (_, i) => (
        <Skeleton key={i} i={i} className={`h-4 rounded-full ${widths[i % widths.length]}`} />
      ))}
    </SkeletonGroup>
  );
}
