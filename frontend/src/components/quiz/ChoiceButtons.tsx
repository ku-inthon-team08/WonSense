"use client";

export function ChoiceButtons<T extends string>({
  options,
  onPick,
}: {
  options: { value: T; label: string }[];
  onPick: (value: T) => void;
}) {
  return (
    <div className="grid grid-cols-2 gap-2">
      {options.map((o) => (
        <button
          key={o.value}
          onClick={() => onPick(o.value)}
          className="rounded-xl border-2 border-brand bg-white px-3 py-3 text-base font-semibold text-slate-800 transition-colors hover:bg-brand-pale active:scale-95"
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}
