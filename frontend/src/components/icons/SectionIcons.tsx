// 홈 카드 제목 앞 아이콘들. Inherits color from `currentColor`, so set it with a text-* class.
const base = { viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 2.5, strokeLinecap: "round", strokeLinejoin: "round" } as const;

export function QuizIcon({ className }: { className?: string }) {
  return (
    <svg {...base} aria-hidden className={className}>
      <path d="M9.2 9a3 3 0 1 1 4.3 2.7c-.9.4-1.5 1.2-1.5 2.2v.4" />
      <path d="M12 18h.01" />
    </svg>
  );
}

export function ChartIcon({ className }: { className?: string }) {
  return (
    <svg {...base} aria-hidden className={className}>
      <path d="M6 20v-6M12 20V8M18 20V4" />
    </svg>
  );
}

export function ExchangeIcon({ className }: { className?: string }) {
  return (
    <svg {...base} aria-hidden className={className}>
      <path d="M4 9h14l-4-4M20 15H6l4 4" />
    </svg>
  );
}

export function StarIcon({ className }: { className?: string }) {
  return (
    <svg {...base} aria-hidden className={className}>
      <path d="m12 4 2.4 5 5.4.6-4 3.7 1.1 5.3L12 16l-4.9 2.6 1.1-5.3-4-3.7 5.4-.6z" />
    </svg>
  );
}

export function ArrowRightIcon({ className }: { className?: string }) {
  return (
    <svg {...base} aria-hidden className={className}>
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  );
}
