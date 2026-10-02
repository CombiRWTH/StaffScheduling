// Planning selection URL format shared by server pages and client components: `?month=YYYY-MM&stations=1,2`.

export const MONTHS = [
  "Januar",
  "Februar",
  "März",
  "April",
  "Mai",
  "Juni",
  "Juli",
  "August",
  "September",
  "Oktober",
  "November",
  "Dezember",
];

/** The selection's `YYYY-MM` month of a year and month number. */
export function selectionMonth(year: number, month: number) {
  return `${year}-${String(month).padStart(2, "0")}`;
}

/** The query string for a selection, or "" when nothing is selected. */
export function selectionSearch(month?: string | null, stations?: readonly number[] | string | null): string {
  const query = new URLSearchParams();
  if (month) query.set("month", month);
  const stationValue = typeof stations === "string" ? stations : stations?.join(",");
  if (stationValue) query.set("stations", stationValue);
  return query.size ? `?${query}` : "";
}
