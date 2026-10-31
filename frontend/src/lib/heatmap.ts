import { api } from "@/lib/api";

// GET /api/heatmap
export type HeatmapDistrict = {
  region: string; // 행정표준 시군구 코드 (예: 11680)
  name: string;
  index: number; // 서울 평균 = 100
  diff_pct: number;
  price_avg: number | null; // 품목 하나를 골랐을 때만 값이 있음
  item_count: number;
};
export type HeatmapResponse = {
  item_id: number | null;
  reference_date: string;
  source: string;
  districts: HeatmapDistrict[];
};

// GET /api/heatmap/items
export type HeatmapItem = { item_id: number; name: string; unit: string; seoul_avg: number };
export type HeatmapItemsResponse = { reference_date: string; items: HeatmapItem[] };

// GET /api/heatmap/districts/{region}
export type DistrictItem = {
  item_id: number;
  name: string;
  unit: string;
  price_avg: number;
  seoul_avg: number;
  diff_pct: number;
};
export type DistrictDetail = { region: string; name: string; reference_date: string; items: DistrictItem[] };

export const getHeatmap = (itemId: number | null, init?: RequestInit) =>
  api<HeatmapResponse>(itemId == null ? "/api/heatmap" : `/api/heatmap?item_id=${itemId}`, init);
export const getHeatmapItems = (init?: RequestInit) => api<HeatmapItemsResponse>("/api/heatmap/items", init);
export const getDistrictDetail = (region: string, init?: RequestInit) =>
  api<DistrictDetail>(`/api/heatmap/districts/${region}`, init);

// 서울 평균 대비 차이(%)를 색 단계로 나눈다. 파랑 = 싸다, 회색 = 평균, 빨강 = 비싸다 (발산형, 양쪽 3단계)
export type Bin = { fill: string; ink: string; label: string };

const CHEAP = ["#1c5cab", "#5598e7", "#b7d3f6"]; // 진함 → 옅음
const PRICEY = ["#f6c4c1", "#e66767", "#b52f2f"]; // 옅음 → 진함
const NEUTRAL = "#f0efec";
const DARK_INK = "#0b0b0b";
const LIGHT_INK = "#ffffff";

// 전체 지수는 구 사이 차이가 작고(±6% 안팎), 품목 하나는 차이가 커서 경계를 다르게 둔다
const THRESHOLDS = { overall: [1, 2.5, 5], item: [2, 5, 10] } as const;

export type ScaleMode = keyof typeof THRESHOLDS;

// 색 단계 사이 경계값 6개 (범례 눈금): −c, −b, −a, +a, +b, +c
export function ticksFor(mode: ScaleMode): string[] {
  const [a, b, c] = THRESHOLDS[mode];
  return [`−${c}%`, `−${b}%`, `−${a}%`, `+${a}%`, `+${b}%`, `+${c}%`];
}

export function binsFor(mode: ScaleMode): Bin[] {
  const [a, b, c] = THRESHOLDS[mode];
  return [
    { fill: CHEAP[0], ink: LIGHT_INK, label: `−${c}% 이하` },
    { fill: CHEAP[1], ink: DARK_INK, label: `−${b}~${c}%` },
    { fill: CHEAP[2], ink: DARK_INK, label: `−${a}~${b}%` },
    { fill: NEUTRAL, ink: DARK_INK, label: `±${a}%` },
    { fill: PRICEY[0], ink: DARK_INK, label: `+${a}~${b}%` },
    { fill: PRICEY[1], ink: DARK_INK, label: `+${b}~${c}%` },
    { fill: PRICEY[2], ink: LIGHT_INK, label: `+${c}% 이상` },
  ];
}

export function binFor(diffPct: number, mode: ScaleMode): Bin {
  const [a, b, c] = THRESHOLDS[mode];
  const bins = binsFor(mode);
  if (diffPct <= -c) return bins[0];
  if (diffPct <= -b) return bins[1];
  if (diffPct <= -a) return bins[2];
  if (diffPct < a) return bins[3];
  if (diffPct < b) return bins[4];
  if (diffPct < c) return bins[5];
  return bins[6];
}

export const formatPct = (v: number) => `${v > 0 ? "+" : v < 0 ? "−" : "±"}${Math.abs(v).toFixed(1)}%`;
export const formatWon = (v: number) => `₩${v.toLocaleString("ko-KR")}`;
