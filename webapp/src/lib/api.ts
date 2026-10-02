import "server-only";
import type {
  AvailabilityEntry,
  DemandCell,
  DemandConfiguration,
  EmployeeCalendar,
  EmployeeSummary,
  GenerationJob,
  MonthlyDemand,
  PatternRequirement,
  PlanningInspection,
  PlanningOptions,
  BundleProblem,
  ScheduleReview,
  WishEntry,
} from "@/lib/types";

const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";

const INVALID_SELECTION = "Ungültige Auswahl. Nur Stationen mit Planungsziel für diesen Monat wählen.";
const INCOMPLETE = "Daten unvollständig. Stationen, Zuordnungen, Monatskonten und Abwesenheiten prüfen.";

/** A failed API call: a German message for the user and the HTTP status for callers that handle one. */
class ApiError extends Error {
  constructor(
    message: string,
    readonly status?: number,
  ) {
    super(message);
  }
}

/**
 * One API call; failures become `ApiError`s, `invalid` and `incomplete` describing a 422 and 409 for this call.
 * A `FormData` body is sent as multipart; `problems` names a 422 by the `problem` code in its body.
 */
async function request<T>(
  method: "GET" | "PUT" | "POST" | "DELETE",
  path: string,
  {
    params,
    body,
    invalid = INVALID_SELECTION,
    incomplete = INCOMPLETE,
    problems,
  }: {
    params?: URLSearchParams;
    body?: unknown;
    invalid?: string;
    incomplete?: string;
    problems?: Record<string, string>;
  } = {},
): Promise<T> {
  const json = body !== undefined && !(body instanceof FormData);
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}${params ? `?${params}` : ""}`, {
      method,
      headers: json ? { "Content-Type": "application/json" } : undefined,
      body: json ? JSON.stringify(body) : (body as FormData | undefined),
      cache: "no-store",
      signal: AbortSignal.timeout(10_000),
    });
  } catch {
    throw new ApiError("Backend nicht erreichbar. Verbindung und Einrichtung prüfen.");
  }
  if (response.status === 422) {
    const problem = problems && (await response.json().catch(() => null))?.problem;
    throw new ApiError(problems?.[problem] ?? invalid, 422);
  }
  if (response.status === 409) throw new ApiError(incomplete, 409);
  if (!response.ok) throw new ApiError(await unavailableMessage(response), response.status);
  return response.status === 204 ? (undefined as T) : response.json();
}

/** A failed TimeOffice query (schema, permissions) is told apart from an unreachable backend or database. */
async function unavailableMessage(response: Response) {
  const body = await response.json().catch(() => null);
  if (body?.integration === "timeoffice" && body.stage === "query") {
    return "TimeOffice-Abfrage fehlgeschlagen. Datenbankschema und Berechtigungen prüfen.";
  }
  return "Backend oder TimeOffice nicht verfügbar. Verbindung und Einrichtung prüfen.";
}

/** The `YYYY-MM` selection month as the API's year and month numbers. */
function planningMonth(month: string) {
  const [year, monthNumber] = month.split("-").map(Number);
  return { year, month: monthNumber };
}

function monthQuery(month: string) {
  const { year, month: monthNumber } = planningMonth(month);
  return new URLSearchParams({ year: String(year), month: String(monthNumber) });
}

function selectionQuery(month: string, stationIds: number[]) {
  const params = monthQuery(month);
  for (const id of stationIds) params.append("planning_unit_ids", String(id));
  return params;
}

/** PUT an entry at `path`, or DELETE it when `entry` is `null`. */
function putOrDelete(path: string, entry: object | null, invalid: string) {
  return entry ? request<void>("PUT", path, { body: entry, invalid }) : request<void>("DELETE", path, { invalid });
}

export function getPlanningOptions(month: string) {
  return request<PlanningOptions>("GET", "/planning/options", { params: monthQuery(month) });
}

export function getEmployees(month: string, stationIds: number[]) {
  return request<PlanningInspection>("GET", "/employees", { params: selectionQuery(month, stationIds) });
}

/** The selection's employees by name; unlike `getEmployees` it needs no complete monthly accounts. */
export function getPlanningEmployees(month: string, stationIds: number[]) {
  return request<EmployeeSummary[]>("GET", "/planning/employees", { params: selectionQuery(month, stationIds) });
}

const INVALID_ENTRY = "Eintrag ungültig. Mitarbeiter, Datum, Art und Schichten prüfen.";

export function getEmployeeCalendar(month: string, employeeId: number) {
  const params = monthQuery(month);
  params.set("employee_id", String(employeeId));
  return request<EmployeeCalendar>("GET", "/availability", { params, invalid: INVALID_ENTRY });
}

/** Replace the employee's availability on that date; `null` removes it. */
export function setAvailability(employeeId: number, date: string, entry: AvailabilityEntry | null) {
  return putOrDelete(`/availability/${employeeId}/${date}`, entry, INVALID_ENTRY);
}

/** Replace the employee's wish on that date; `null` removes it. */
export function setWish(employeeId: number, date: string, entry: WishEntry | null) {
  return putOrDelete(`/wishes/${employeeId}/${date}`, entry, INVALID_ENTRY);
}

const INVALID_DEMAND = "Mindestbesetzung ungültig. Station, Datum, Schichten und Anzahlen (0–99) prüfen.";

export function getDemand(month: string, stationId: number) {
  const params = monthQuery(month);
  params.set("planning_unit_id", String(stationId));
  return request<DemandConfiguration>("GET", "/demand", { params, invalid: INVALID_DEMAND });
}

export function putDemand(month: string, stationId: number, cells: DemandCell[]) {
  const body = { planning_unit_id: stationId, planning_month: planningMonth(month), cells };
  return request<MonthlyDemand>("PUT", "/demand", { body, invalid: INVALID_DEMAND });
}

export function previewPattern(month: string, stationId: number, cells: PatternRequirement[]) {
  const body = { planning_unit_id: stationId, planning_month: planningMonth(month), cells };
  return request<MonthlyDemand>("POST", "/demand/pattern", { body, invalid: INVALID_DEMAND });
}

const INVALID_GENERATION = "Generierung ungültig. Stationen mit Planungsziel und eine Laufzeit von 1–3600 s wählen.";
const INCOMPLETE_GENERATION =
  "Eingaben unvollständig. Mindestbesetzung jeder Station speichern und Mitarbeiterdaten prüfen.";

/** Validate the full month's input and start solving it; the job runs on in the backend. */
export async function startGeneration(month: string, stationIds: number[], timeoutSeconds: number) {
  const body = { planning_unit_ids: stationIds, planning_month: planningMonth(month), timeout_seconds: timeoutSeconds };
  try {
    return await request<GenerationJob>("POST", "/generation", {
      body,
      invalid: INVALID_GENERATION,
      incomplete: INCOMPLETE_GENERATION,
    });
  } catch (error) {
    // 423: the backend solves one generation at a time.
    if (error instanceof ApiError && error.status === 423) {
      throw new ApiError("Es läuft bereits eine Generierung. Nach ihrem Ende erneut starten.", 423);
    }
    throw error;
  }
}

/** The latest generation since the API started, or `null` if there is none (also after a restart). */
export async function getLatestGeneration(): Promise<GenerationJob | null> {
  try {
    return await request<GenerationJob>("GET", "/generation");
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

/** The schedule under review, or `null` without one (also after a restart). */
export async function getReview(): Promise<ScheduleReview | null> {
  try {
    return await request<ScheduleReview>("GET", "/review");
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

const IMPORT_PROBLEMS: Record<BundleProblem, string> = {
  malformed: "Dateien ungültig. input.json und result.json im Format Version 1 wählen.",
  mismatch: "Dateien passen nicht zusammen. result.json gehört zu einer anderen input.json oder einem anderen Monat.",
  no_schedule: "result.json enthält keinen Dienstplan.",
  references:
    "result.json enthält Dienste unbekannter Mitarbeiter, Stationen oder Schichten oder außerhalb des Monats.",
  check: "Die Prüfung in result.json weicht von der unabhängigen Prüfung ab.",
};

/** Review an uploaded `input`/`result` pair; a rejected pair leaves the current review unchanged. */
export function importReview(files: FormData) {
  return request<ScheduleReview>("POST", "/review/import", {
    body: files,
    invalid: IMPORT_PROBLEMS.malformed,
    problems: IMPORT_PROBLEMS,
  });
}

/** The downloadable files of the schedule under review. */
export const REVIEW_FILES = ["input.json", "result.json", "schedule.csv", "employees.csv"] as const;
export type ReviewFile = (typeof REVIEW_FILES)[number];

/** One file of the schedule under review as the API's response, or `null` without a review. */
export async function getReviewFile(name: ReviewFile): Promise<Response | null> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}/review/files/${name}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(10_000),
    });
  } catch {
    throw new ApiError("Backend nicht erreichbar. Verbindung und Einrichtung prüfen.");
  }
  if (response.status === 404) return null;
  if (!response.ok) throw new ApiError(await unavailableMessage(response), response.status);
  return response;
}

export async function isApiHealthy() {
  try {
    const response = await fetch(`${API_URL}/status`, { signal: AbortSignal.timeout(5_000) });
    return response.ok && (await response.json()).status === "healthy";
  } catch {
    return false;
  }
}
