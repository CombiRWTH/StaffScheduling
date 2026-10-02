// German labels for canonical values, and locale-independent date text shared by server and client.
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
