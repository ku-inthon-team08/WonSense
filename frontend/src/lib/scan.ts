// Price-tag scan — types and calls for backend/app/routers/scan.py
import { api } from "@/lib/api";

export type Verdict = "cheap" | "fair" | "pricey" | "ripoff";
export type Ingredient = "pork" | "beef" | "chicken" | "seafood" | "egg" | "dairy" | "wheat" | "nuts" | "soy" | "alcohol";

export type ScanLine = {
  name: string; // as written in the photo
  name_en: string;
  price: number;
  quantity: string | null;
  // menu translation — present on every line
  description_en: string | null;
  spice_level: 0 | 1 | 2 | 3 | null; // null = not food
  contains: Ingredient[];
  vegetarian: boolean | null; // null = unsure / not food
  matched: boolean;
  // only when matched
  basis?: "official" | "menu" | "estimate"; // Seoul grocery data / Seoul good-price restaurant menus / Numbeo estimate
  store_count?: number; // menu: how many stores the price range comes from
  item_id?: number | null;
  catalog_name?: string;
  catalog_unit?: string | null;
  quantity_ratio?: number;
  seoul_avg?: number; // scaled to the photo's quantity
  seoul_range?: [number | null, number | null];
  seoul_diff_pct?: number;
  compare_avg?: number; // the average the verdict uses: chosen district's, else Seoul's
  compare_region?: string | null; // district name, null = Seoul
  diff_pct?: number; // vs compare_avg
  verdict?: Verdict;
  district_avg?: number | null;
  district_prices?: Record<string, number>; // every district's average, scaled — lets us re-judge locally
  cheapest_district?: { region: string; name: string; price_avg: number } | null;
  source?: string;
  reference_date?: string;
};

export type ScanSummary = {
  matched_count: number;
  total_price: number | null;
  total_avg: number | null;
  diff_pct: number | null;
  verdict: Verdict | null;
};

export type ScanResponse = { lines: ScanLine[]; summary: ScanSummary };

export const scanPhoto = (image: string, district: string | null) =>
  api<ScanResponse>("/api/scan", {
    method: "POST",
    body: JSON.stringify({ image, media_type: "image/jpeg", district }),
  });

// Same bands as backend/app/services/scan.py
const FAIR_BAND = 0.1;
const RIPOFF = 0.3;

export function verdictOf(diff: number): Verdict {
  if (diff < -FAIR_BAND) return "cheap";
  if (diff <= FAIR_BAND) return "fair";
  return diff <= RIPOFF ? "pricey" : "ripoff";
}

const pct = (diff: number) => Math.round(diff * 1000) / 10;

/** Re-judge a scan against another district without calling Claude again.
 *  Lines with no data for that district (Numbeo estimates, missing districts) stay on the Seoul average. */
export function rejudge(result: ScanResponse, district: string): ScanResponse {
  const lines = result.lines.map((line): ScanLine => {
    if (!line.matched || line.seoul_avg === undefined) return line;
    const local = district ? line.district_prices?.[district] : undefined;
    const avg = local ?? line.seoul_avg;
    const diff = line.price / avg - 1;
    return {
      ...line,
      compare_avg: avg,
      compare_region: local ? district : null,
      district_avg: local ?? null,
      diff_pct: pct(diff),
      verdict: verdictOf(diff),
    };
  });
  const matched = lines.filter((l) => l.matched && l.compare_avg !== undefined);
  if (matched.length === 0) return { lines, summary: result.summary };
  const paid = matched.reduce((sum, l) => sum + l.price, 0);
  const avg = matched.reduce((sum, l) => sum + l.compare_avg!, 0);
  const diff = paid / avg - 1;
  return {
    lines,
    summary: { matched_count: matched.length, total_price: paid, total_avg: avg, diff_pct: pct(diff), verdict: verdictOf(diff) },
  };
}

const MAX_SIDE = 1600; // enough to read price tags, keeps uploads well under the 5MB limit

/** Phone photos are often 5MB+: shrink to JPEG on a canvas and return a data URL. */
export async function shrinkPhoto(file: File): Promise<string> {
  const bitmap = await createImageBitmap(file);
  const scale = Math.min(1, MAX_SIDE / Math.max(bitmap.width, bitmap.height));
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(bitmap.width * scale);
  canvas.height = Math.round(bitmap.height * scale);
  canvas.getContext("2d")!.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  bitmap.close();
  return canvas.toDataURL("image/jpeg", 0.85);
}
