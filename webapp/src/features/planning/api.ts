import "server-only";
import { z } from "zod";
import { getSolverApiConfig } from "@/lib/config/app-config";

export async function readPlanningApi<T>(path: string, params: URLSearchParams, schema: z.ZodType<T>): Promise<T> {
  try {
    const response = await fetch(`${getSolverApiConfig().baseUrl}${path}?${params}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(10_000),
    });
    if (!response.ok) {
      if (response.status === 409)
        throw new Error("Daten unvollständig. Stationen, Mitgliedschaften, Konten und Monatsnachweise prüfen.");
      throw new Error("Backend oder TimeOffice nicht verfügbar. Verbindung und Einrichtung prüfen.");
    }
    const parsed = schema.safeParse(await response.json());
    if (!parsed.success) throw new Error("Backend-Daten unvollständig oder ungültig. Einrichtung prüfen.");
    return parsed.data;
  } catch (error) {
    if (error instanceof Error && /prüfen\.$/.test(error.message)) throw error;
    throw new Error("Backend oder TimeOffice nicht verfügbar. Verbindung und Einrichtung prüfen.");
  }
}

export function monthParams(month: string): URLSearchParams {
  if (!/^(20\d{2}|21\d{2}|2200)-(0[1-9]|1[0-2])$/.test(month))
    throw new Error("Bitte einen gültigen Planungsmonat wählen.");
  const [year, monthNumber] = month.split("-");
  return new URLSearchParams({ year, month: String(Number(monthNumber)) });
}
