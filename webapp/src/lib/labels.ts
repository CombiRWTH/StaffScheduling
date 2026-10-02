// German labels for canonical values, and locale-independent date text shared by server and client.
import { MONTHS } from "@/lib/selection";
import type { AvailabilityType, StaffLevel, WishType } from "@/lib/types";

export const STAFF_LEVEL_LABELS: Record<StaffLevel, string> = {
  professional: "Fachkraft",
  assistant: "Hilfskraft",
  trainee: "Azubi",
  mfa: "MFA",
};

export const AVAILABILITY_LABELS: Record<AvailabilityType, string> = {
  unavailable: "Nicht verfügbar",
  vacation: "Urlaub",
  training: "Fortbildung",
  free_day: "Frei",
  available_only: "Nur bestimmte Schichten",
};

export const WISH_LABELS: Record<WishType, string> = {
  free_day: "Freier Tag",
  free_shift: "Schicht frei",
  preferred_day: "Wunschtag",
  preferred_shift: "Wunschschicht",
};

export const WEEKDAYS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"];

/** `DD.MM.YYYY` from an ISO date's text, so server and browser render identically regardless of locale. */
export function formatDate(value: string) {
  const [year, month, day] = value.split("-");
  return `${day}.${month}.${year}`;
}

/** A planning month's name and its first to last date, e.g. "Juni 2026" and "01.06.2026–30.06.2026". */
export function monthLabel(year: number, month: number) {
  const last = new Date(Date.UTC(year, month, 0)).getUTCDate();
  const prefix = `${year}-${String(month).padStart(2, "0")}`;
  return {
    name: `${MONTHS[month - 1]} ${year}`,
    range: `${formatDate(`${prefix}-01`)}–${formatDate(`${prefix}-${last}`)}`,
  };
}
