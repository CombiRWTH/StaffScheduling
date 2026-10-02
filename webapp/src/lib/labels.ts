// German labels for canonical values, and locale-independent date text shared by server and client.
import { MONTHS, selectionMonth } from "@/lib/selection";
import type { AvailabilityType, CheckStatus, Rule, ShiftType, SolutionStatus, StaffLevel, WishType } from "@/lib/types";

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

/** What the solver found, with a short explanation. */
export const SOLVER_STATUS: Record<SolutionStatus, [string, string]> = {
  optimal: ["Optimale Lösung", "Bestmöglich nach den umgesetzten Regeln"],
  feasible: ["Lösung gefunden", "Optimum nicht nachgewiesen"],
  infeasible: ["Keine Lösung möglich", "Eingaben widersprechen sich"],
  unknown: ["Keine Lösung innerhalb der Laufzeit", "Längere Laufzeit versuchen"],
  model_invalid: ["Modell ungültig", "Backend-Protokoll prüfen"],
};

/** The independent schedule check, apart from the solver status. */
export const CHECK_STATUS: Record<CheckStatus, [string, string]> = {
  accepted: ["Regeln eingehalten", "Alle geprüften Regeln erfüllt"],
  rejected: ["Regelverstöße", "Der Plan ist nicht verwendbar"],
  incomplete: ["Unvollständig geprüft", "Für eine Regel fehlen Eingaben"],
};

/** German names of the checked rules, as the backend reports them. */
export const RULES: Record<Rule, string> = {
  input: "Ungültige Dienste",
  staffing: "Mindestbesetzung",
  eligibility: "Zuordnung und Qualifikation",
  one_duty_per_day: "Ein Dienst pro Tag",
  availability: "Verfügbarkeit",
  monthly_balance: "Monatskonto",
  work_and_breaks: "Arbeitszeit und Pausen",
  work_average: "Durchschnittliche Arbeitszeit",
  rest: "Ruhezeit",
  consecutive_nights: "Nächte in Folge",
  night_recovery: "Erholung nach Nachtdiensten",
  replacement_rest: "Ersatzruhetag",
  annual_free_sundays: "Freie Sonntage im Jahr",
};

export const SHIFT_TYPE_LABELS: Record<ShiftType, string> = {
  early: "Früh",
  intermediate: "Zwischen",
  late: "Spät",
  night: "Nacht",
  management: "Leitung",
  other: "Sonstige",
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
  const prefix = selectionMonth(year, month);
  return {
    name: `${MONTHS[month - 1]} ${year}`,
    range: `${formatDate(`${prefix}-01`)}–${formatDate(`${prefix}-${last}`)}`,
  };
}
