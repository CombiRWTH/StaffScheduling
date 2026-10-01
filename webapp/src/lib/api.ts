import "server-only";
import type { PlanningInspection, PlanningOptions } from "@/lib/types";

const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";

async function get<T>(path: string, params: URLSearchParams): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}?${params}`, { signal: AbortSignal.timeout(10_000) });
  } catch {
    throw new Error("Backend nicht erreichbar. Verbindung und Einrichtung prüfen.");
  }
  if (response.status === 409) {
    throw new Error("Daten unvollständig. Stationen, Mitgliedschaften, Konten und Monatsnachweise prüfen.");
  }
  if (!response.ok) throw new Error("Backend oder TimeOffice nicht verfügbar. Verbindung und Einrichtung prüfen.");
  return response.json();
}

function monthQuery(month: string) {
  const [year, monthNumber] = month.split("-");
  return new URLSearchParams({ year, month: String(Number(monthNumber)) });
}

export function getPlanningOptions(month: string) {
  return get<PlanningOptions>("/planning/options", monthQuery(month));
}

export function getEmployees(month: string, stationIds: number[]) {
  const params = monthQuery(month);
  for (const id of stationIds) params.append("planning_unit_ids", String(id));
  return get<PlanningInspection>("/employees", params);
}

export async function isApiHealthy() {
  try {
    const response = await fetch(`${API_URL}/status`, { signal: AbortSignal.timeout(5_000) });
    return response.ok && (await response.json()).status === "healthy";
  } catch {
    return false;
  }
}
