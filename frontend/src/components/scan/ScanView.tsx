"use client";

import { useRef, useState } from "react";

import { CameraIcon } from "@/components/icons/CameraIcon";
import { formatKrw } from "@/lib/reviews";
import { scanPhoto, shrinkPhoto, type ScanLine, type ScanResponse, type Verdict } from "@/lib/scan";
import { SEOUL_DISTRICTS } from "@/lib/seoulDistricts";
import { t } from "@/lib/strings";

const card = "rounded-2xl bg-white p-5 shadow-card";

// Same direction as the heat map: cheap = blue, pricey = red.
const verdictStyle: Record<Verdict, string> = {
  cheap: "bg-sky-50 text-sky-700",
  fair: "bg-emerald-50 text-emerald-700",
  pricey: "bg-amber-50 text-amber-700",
  ripoff: "bg-rose-50 text-rose-700",
};

const districtNames = [...SEOUL_DISTRICTS].map((d) => d.name).sort((a, b) => a.localeCompare(b, "ko"));

type State =
  | { step: "idle" }
  | { step: "reading"; photo: string }
  | { step: "done"; photo: string; result: ScanResponse; district: string }
  | { step: "error"; photo: string | null; message: string };

export function ScanView() {
  const [state, setState] = useState<State>({ step: "idle" });
  const [district, setDistrict] = useState("");
  const cameraInput = useRef<HTMLInputElement>(null);
  const albumInput = useRef<HTMLInputElement>(null);

  async function onFile(file: File | undefined) {
    if (!file) return;
    let photo: string | null = null;
    try {
      photo = await shrinkPhoto(file);
      setState({ step: "reading", photo });
      const result = await scanPhoto(photo, district || null);
      setState({ step: "done", photo, result, district });
    } catch (e) {
      setState({ step: "error", photo, message: (e as Error).message });
    }
  }

  const photo = state.step === "idle" ? null : state.photo;

  return (
    <div className="flex flex-col gap-6">
      <section className={card}>
        <label className="mb-4 flex flex-wrap items-center gap-2 text-sm text-slate-600">
          {t.scan.district}
          <select
            value={district}
            onChange={(e) => setDistrict(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-slate-900 focus:border-brand focus:outline-none"
          >
            <option value="">{t.scan.districtNone}</option>
            {districtNames.map((name) => (
              <option key={name} value={name}>{name}</option>
            ))}
          </select>
        </label>

        {photo ? (
          // eslint-disable-next-line @next/next/no-img-element -- local data URL preview
          <img src={photo} alt="" className="mx-auto max-h-80 w-auto rounded-xl bg-stone-100 object-contain" />
        ) : (
          <button
            type="button"
            onClick={() => cameraInput.current?.click()}
            className="flex w-full flex-col items-center gap-3 rounded-xl bg-stone-100 px-4 py-12 text-slate-600 hover:ring-1 hover:ring-brand/50"
          >
            <CameraIcon className="h-12 w-12 text-brand" />
            <span className="text-base font-medium text-slate-800">{t.scan.takePhoto}</span>
            <span className="text-sm">{t.scan.pageDesc}</span>
          </button>
        )}

        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            disabled={state.step === "reading"}
            onClick={() => cameraInput.current?.click()}
            className="inline-flex items-center gap-2 rounded-lg bg-brand px-4 py-2 font-medium text-white hover:bg-brand/90 disabled:opacity-50"
          >
            <CameraIcon className="h-5 w-5" />
            {photo ? t.scan.retake : t.scan.takePhoto}
          </button>
          <button
            type="button"
            disabled={state.step === "reading"}
            onClick={() => albumInput.current?.click()}
            className="rounded-lg border border-brand px-4 py-2 font-medium text-brand disabled:opacity-50"
          >
            {t.scan.pickPhoto}
          </button>
        </div>

        {/* capture opens the rear camera on phones; desktop browsers fall back to a file picker */}
        <input ref={cameraInput} type="file" accept="image/*" capture="environment" hidden
          onChange={(e) => { void onFile(e.target.files?.[0]); e.target.value = ""; }} />
        <input ref={albumInput} type="file" accept="image/*" hidden
          onChange={(e) => { void onFile(e.target.files?.[0]); e.target.value = ""; }} />
      </section>

      {state.step === "reading" && (
        <p className="py-6 text-center text-slate-500" aria-live="polite">{t.scan.reading}</p>
      )}

      {state.step === "error" && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          <p>{t.scan.error}</p>
          <p className="mt-1 text-xs opacity-80">{state.message}</p>
        </div>
      )}

      {state.step === "done" && <ScanResult result={state.result} district={state.district} />}
    </div>
  );
}

function ScanResult({ result, district }: { result: ScanResponse; district: string }) {
  const { lines, summary } = result;
  if (lines.length === 0) {
    return <p className="py-6 text-center text-slate-500">{t.scan.noPrices}</p>;
  }
  return (
    <div className="flex flex-col gap-3">
      {summary.verdict && summary.matched_count > 1 && (
        <section className={`rounded-2xl p-5 ${verdictStyle[summary.verdict]}`}>
          <p className="text-sm">{t.scan.summary(summary.matched_count)}</p>
          <p className="mt-1 text-2xl font-bold">{t.scan.verdict[summary.verdict]}</p>
          <p className="mt-1 text-sm">
            {formatKrw(summary.total_price!)} · {t.scan.diff(summary.diff_pct!)}
          </p>
        </section>
      )}
      <ul className="flex flex-col gap-3">
        {lines.map((line, i) => (
          <li key={i}>
            <LineCard line={line} district={district} />
          </li>
        ))}
      </ul>
      <p className="text-xs text-slate-500">{t.scan.note}</p>
    </div>
  );
}

function LineCard({ line, district }: { line: ScanLine; district: string }) {
  const [low, high] = line.seoul_range ?? [null, null];
  return (
    <article className={card}>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="font-semibold">{line.name}</h3>
          <p className="text-sm text-slate-500">
            {line.name_en}
            {line.quantity && ` · ${line.quantity}`}
          </p>
        </div>
        {line.verdict && (
          <span className={`rounded-full px-3 py-1 text-sm font-semibold ${verdictStyle[line.verdict]}`}>
            {t.scan.verdict[line.verdict]}
          </span>
        )}
      </div>

      {!line.matched ? (
        <p className="mt-3 text-sm text-slate-500">
          {t.scan.paid} <span className="font-semibold text-slate-900">{formatKrw(line.price)}</span> · {t.scan.unmatched}
        </p>
      ) : (
        <>
          <dl className="mt-3 grid grid-cols-2 gap-3 rounded-xl bg-stone-100 p-4 text-sm">
            <div>
              <dt className="text-slate-500">{t.scan.paid}</dt>
              <dd className="text-lg font-bold">{formatKrw(line.price)}</dd>
            </div>
            <div>
              <dt className="text-slate-500">{t.scan.seoulAvg}</dt>
              <dd className="text-lg font-bold">{formatKrw(line.seoul_avg!)}</dd>
            </div>
            {low !== null && high !== null && (
              <div>
                <dt className="text-slate-500">{t.scan.range}</dt>
                <dd>{formatKrw(low)} ~ {formatKrw(high)}</dd>
              </div>
            )}
            {district && line.district_avg && (
              <div>
                <dt className="text-slate-500">{t.scan.districtAvg(district)}</dt>
                <dd>{formatKrw(line.district_avg)}</dd>
              </div>
            )}
          </dl>
          <p className="mt-2 text-sm font-medium">{t.scan.diff(line.diff_pct!)}</p>
          {line.cheapest_district && (
            <p className="mt-1 text-sm text-slate-600">
              {t.scan.cheapest(line.cheapest_district.name, formatKrw(line.cheapest_district.price_avg))}
            </p>
          )}
          <p className="mt-3 text-xs text-slate-500">
            {t.scan.comparedTo}: {line.catalog_name}
            {line.quantity_ratio && line.quantity_ratio !== 1 && ` ×${line.quantity_ratio}`} ·{" "}
            {line.basis === "official" ? t.scan.basisOfficial : t.scan.basisEstimate} · {t.scan.source}: {line.source}
            {line.reference_date && ` (${line.reference_date})`}
          </p>
        </>
      )}
    </article>
  );
}
