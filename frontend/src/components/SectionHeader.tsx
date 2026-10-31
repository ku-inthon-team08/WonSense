import Link from "next/link";

export function SectionHeader({ num, title, href }: { num: number; title: string; href: string }) {
  return (
    <Link href={href} className="group mb-3 flex items-center gap-2 text-lg font-semibold">
      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-600 text-xs text-white">
        {num}
      </span>
      {title}
      <span className="text-indigo-600 transition-transform group-hover:translate-x-1">→</span>
    </Link>
  );
}
