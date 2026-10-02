// German labels for canonical values, and locale-independent date text shared by server and client.
import { MONTHS, selectionMonth } from "@/lib/selection";
import type {
  AvailabilityType,
  CheckStatus,
  Rule,
  ScheduleCheck,
  ShiftType,
  Solution,
  SolutionStatus,
  Stage,
  StaffLevel,
  WishStatus,
  WishType,
} from "@/lib/types";

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

/** What a schedule made of a wish. */
export const WISH_STATUS_LABELS: Record<WishStatus, string> = {
  granted: "erfüllt",
  denied: "nicht erfüllt",
  not_grantable: "nicht erfüllbar",
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

const NUMBER = new Intl.NumberFormat("de-DE", { maximumFractionDigits: 1 });

/** The solver status with its explanation, e.g. "Lösung gefunden (Optimum nicht nachgewiesen)". */
export function solverStatusText(status: SolutionStatus) {
  const [value, detail] = SOLVER_STATUS[status];
  return `${value} (${detail})`;
}

/** The objective tiers in the check's scores, named for the staff admin. */
export const OBJECTIVE_LABELS: Record<Stage["name"], string> = {
  gaps: "Lücken",
  health_events: "Gesundheitsereignisse",
  station_transfers: "Einsätze anderer Station",
  wish_cost: "Wunschkosten (Fairness)",
  six_day_windows: "Sechs-Tage-Folgen",
  backward_transitions: "Rückwärtswechsel",
  balance_deviation_minutes: "Abweichung der Monatskonten (Minuten)",
  surplus_intermediate_duties: "Überzählige Zwischendienste",
};

/** One stage's value and whether it is proven best, e.g. "870 (Schranke 0, nicht nachgewiesen)". */
export function formatStage(stage: Stage) {
  return stage.status === "optimal"
    ? `${stage.value} (optimal)`
    : `${stage.value} (Schranke ${NUMBER.format(stage.best_bound)}, nicht nachgewiesen)`;
}

/** How many objective stages proved their optimum, e.g. "2 von 3 optimal". */
export function formatStages(stages: Stage[]) {
  if (stages.length === 0) return "–";
  return `${stages.filter((stage) => stage.status === "optimal").length} von ${stages.length} optimal`;
}

/** Solver search time used against its limit, e.g. "3,1 von 30 s". */
export function formatSearchTime(seconds: number, limit: number) {
  return `${NUMBER.format(seconds)} von ${limit} s`;
}

/**
 * The check's rules that the input cannot decide, as "rule date–date": `missing` lacks input and blocks
 * acceptance, `later` lies beyond the month and does not.
 */
export function missingInputs(check: ScheduleCheck | null | undefined) {
  const text = (row: ScheduleCheck["not_assessed"][number]) =>
    `${RULES[row.rule]} ${formatDate(row.start)}–${formatDate(row.end)}`;
  const rows = check?.not_assessed ?? [];
  return {
    missing: rows.filter((row) => row.blocking).map(text),
    later: rows.filter((row) => !row.blocking).map(text),
  };
}

// What a solver diagnostic means for the staff admin; the backend's English detail stays for developers.
const DIAGNOSTIC_HINTS: Record<string, (count: number) => string> = {
  "staffing.too_few_candidates": (count) =>
    `Mindestbesetzung nicht erreichbar: Für ${count} ${count === 1 ? "Schicht" : "Schichten"} gibt es zu wenige einsetzbare Mitarbeiter; sie bleiben als Lücken offen. Mindestbesetzung, Verfügbarkeit und Zuordnungen prüfen.`,
  "balance.unreachable": (count) =>
    `Monatskonto nicht erreichbar: ${count} ${count === 1 ? "Mitarbeiter kann" : "Mitarbeiter können"} keinen Dienst übernehmen, ${count === 1 ? "hat" : "haben"} aber Soll-Stunden. Verfügbarkeit und Zuordnungen prüfen.`,
  "shift.breaks_rules": (count) =>
    `${count} ${count === 1 ? "Schicht verletzt" : "Schichten verletzen"} an einem Tag die Arbeitszeitregeln und ${count === 1 ? "wird" : "werden"} nie vergeben.`,
  "cp_sat.model_invalid": () => "Das Solver-Modell ist ungültig; Details stehen im Backend-Protokoll.",
};

/** The solver's warnings and errors in German, one line per kind with its count. */
export function diagnosticHints(diagnostics: Solution["diagnostics"]) {
  const counts = new Map<string, number>();
  for (const row of diagnostics) if (row.severity !== "info") counts.set(row.code, (counts.get(row.code) ?? 0) + 1);
  return [...counts].map(([code, count]) =>
    code in DIAGNOSTIC_HINTS
      ? DIAGNOSTIC_HINTS[code](count)
      : `${count} weitere Solver-Hinweise; Details unter Technische Details.`,
  );
}

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

/** Minutes as hours and minutes, the way staff read work accounts, e.g. "160:00 h"; `signed` adds + or −. */
export function formatHours(minutes: number, { signed = false } = {}) {
  const sign = minutes < 0 ? "−" : signed && minutes > 0 ? "+" : "";
  const total = Math.abs(minutes);
  return `${sign}${Math.floor(total / 60)}:${String(total % 60).padStart(2, "0")} h`;
}

/** `DD.MM.YYYY` from an ISO date's text, so server and browser render identically regardless of locale. */
export function formatDate(value: string) {
  const [year, month, day] = value.split("-");
  return `${day}.${month}.${year}`;
}

/** `monthLabel` of a selection month in its URL form, `YYYY-MM`. */
export function selectionMonthLabel(month: string) {
  const [year, number] = month.split("-").map(Number);
  return monthLabel(year, number);
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
