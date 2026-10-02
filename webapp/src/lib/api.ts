import "server-only";
import type {
  AvailabilityEntry,
  DemandConfiguration,
  EmployeeCalendar,
  MonthlyDemand,
  PatternRequirement,
  PlanningInspection,
  PlanningOptions,
  WishEntry,
} from "@/lib/types";

const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";

const INVALID_SELECTION = "Ungültige Auswahl. Nur Stationen mit Planungsziel für diesen Monat wählen.";
const INCOMPLETE = "Daten unvollständig. Stationen, Zuordnungen, Konten und Monatsnachweise prüfen.";

/** One API call; failures become German messages, `invalid` describing a 422 for this call. */
async function request<T>(
  method: "GET" | "PUT" | "POST" | "DELETE",
  path: string,
  { params, body, invalid = INVALID_SELECTION }: { params?: URLSearchParams; body?: unknown; invalid?: string } = {},
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}${params ? `?${params}` : ""}`, {
      method,
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      cache: "no-store",
      signal: AbortSignal.timeout(10_000),
    });
  } catch {
    throw new Error("Backend nicht erreichbar. Verbindung und Einrichtung prüfen.");
  }
  if (response.status === 422) throw new Error(invalid);
  if (response.status === 409) throw new Error(INCOMPLETE);
  if (!response.ok) throw new Error("Backend oder TimeOffice nicht verfügbar. Verbindung und Einrichtung prüfen.");
  return response.status === 204 ? (undefined as T) : response.json();
}

function monthQuery(month: string) {
  const [year, monthNumber] = month.split("-");
  return new URLSearchParams({ year, month: String(Number(monthNumber)) });
}

function monthBody(month: string) {
  const [year, monthNumber] = month.split("-").map(Number);
  return { year, month: monthNumber };
}

export function getPlanningOptions(month: string) {
  return request<PlanningOptions>("GET", "/planning/options", { params: monthQuery(month) });
}

export function getEmployees(month: string, stationIds: number[]) {
  const params = monthQuery(month);
  for (const id of stationIds) params.append("planning_unit_ids", String(id));
  return request<PlanningInspection>("GET", "/employees", { params });
}

const INVALID_ENTRY = "Eintrag ungültig. Mitarbeiter, Datum, Art und Schichten prüfen.";

export function getEmployeeCalendar(month: string, employeeId: number) {
  const params = monthQuery(month);
  params.set("employee_id", String(employeeId));
  return request<EmployeeCalendar>("GET", "/availability", { params, invalid: INVALID_ENTRY });
}

/** Replace the employee's availability on that date; `null` removes it. */
export function setAvailability(employeeId: number, date: string, entry: AvailabilityEntry | null) {
  const path = `/availability/${employeeId}/${date}`;
  return entry
    ? request<void>("PUT", path, { body: entry, invalid: INVALID_ENTRY })
    : request<void>("DELETE", path, { invalid: INVALID_ENTRY });
}

/** Replace the employee's wish on that date; `null` removes it. */
export function setWish(employeeId: number, date: string, entry: WishEntry | null) {
  const path = `/wishes/${employeeId}/${date}`;
  return entry
    ? request<void>("PUT", path, { body: entry, invalid: INVALID_ENTRY })
    : request<void>("DELETE", path, { invalid: INVALID_ENTRY });
}

const INVALID_DEMAND = "Mindestbesetzung ungültig. Station, Datum, Schichten und Anzahlen prüfen.";

export function getDemand(month: string, stationId: number) {
  const params = monthQuery(month);
  params.set("planning_unit_id", String(stationId));
  return request<DemandConfiguration>("GET", "/demand", { params, invalid: INVALID_DEMAND });
}

export function putDemand(month: string, stationId: number, requirements: MonthlyDemand["requirements"]) {
  const body = { planning_unit_id: stationId, planning_month: monthBody(month), requirements };
  return request<MonthlyDemand>("PUT", "/demand", { body, invalid: INVALID_DEMAND });
}

export function previewPattern(month: string, stationId: number, cells: PatternRequirement[]) {
  const body = { planning_unit_id: stationId, planning_month: monthBody(month), cells };
  return request<MonthlyDemand>("POST", "/demand/pattern", { body, invalid: INVALID_DEMAND });
}

export async function isApiHealthy() {
  try {
    const response = await fetch(`${API_URL}/status`, { signal: AbortSignal.timeout(5_000) });
    return response.ok && (await response.json()).status === "healthy";
  } catch {
    return false;
  }
}
