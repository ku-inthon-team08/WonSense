// Price-tag scan — types and calls for backend/app/routers/scan.py
import { api } from "@/lib/api";

export type Verdict = "cheap" | "fair" | "pricey" | "ripoff";

export type ScanLine = {
  name: string; // as written in the photo
  name_en: string;
  price: number;
  quantity: string | null;
  matched: boolean;
  // only when matched
  basis?: "official" | "estimate"; // Seoul city grocery data / Numbeo estimate
  item_id?: number | null;
  catalog_name?: string;
  catalog_unit?: string | null;
  quantity_ratio?: number;
  seoul_avg?: number; // scaled to the photo's quantity
  seoul_range?: [number | null, number | null];
  diff_pct?: number;
  verdict?: Verdict;
  district_avg?: number | null;
  cheapest_district?: { region: string; name: string; price_avg: number } | null;
  source?: string;
  reference_date?: string;
};

export type ScanSummary = {
  matched_count: number;
  total_price: number | null;
  total_seoul_avg: number | null;
  diff_pct: number | null;
  verdict: Verdict | null;
};

export type ScanResponse = { lines: ScanLine[]; summary: ScanSummary };

export const scanPhoto = (image: string, district: string | null) =>
  api<ScanResponse>("/api/scan", {
    method: "POST",
    body: JSON.stringify({ image, media_type: "image/jpeg", district }),
  });

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
