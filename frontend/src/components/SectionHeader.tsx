import Link from "next/link";

export function SectionHeader({ title, href }: { title: string; href: string }) {
  return (
    <Link href={href} className="group mb-3 flex items-center gap-2 text-lg font-semibold">
      <span aria-hidden className="h-2.5 w-2.5 rounded-full bg-brand" />
      {title}
      <span className="text-brand transition-transform group-hover:translate-x-1">→</span>
    </Link>
  );
}
