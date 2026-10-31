export const formatKrw = (n: number) => `₩${n.toLocaleString("ko-KR")}`;

/** "₩8,000 ~ ₩9,000", or just the median when the usual range is a single price. */
export const formatKrwRange = (low: number, median: number, high: number) =>
  low === high ? formatKrw(median) : `${formatKrw(low)} ~ ${formatKrw(high)}`;

export const formatDate = (iso: string, locale = "ko-KR") =>
  new Date(iso).toLocaleDateString(locale, { year: "numeric", month: "short", day: "numeric" });
