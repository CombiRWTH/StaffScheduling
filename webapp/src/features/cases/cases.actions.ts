"use server";

import { getInjection } from "@/di/container";
import { CaseUnit } from "@/entities/models/case.model";
import { getSolverApiConfig } from "@/lib/config/app-config";
import { z } from "zod";

const SolverOptionsSchema = z.object({
  planning_units: z.array(
    z.object({
      planning_unit_id: z.number(),
      display_name: z.string().optional(),
      type: z.string().optional(),
    }),
  ),
});

export async function listCasesAction(): Promise<{ units: CaseUnit[] }> {
  const controller = getInjection("IListCasesController");
  const result = await controller();
  if ("error" in result) throw new Error(result.error);
  return { units: result.data };
}

export async function refreshCasesFromSolverOptionsAction(monthYear: string): Promise<{ units: CaseUnit[] }> {
  const baseUrl = getSolverApiConfig().baseUrl;
  const response = await fetch(`${baseUrl}/solve/options`, { cache: "no-store" });

  if (!response.ok) {
    const message = await response.text().catch(() => "");
    throw new Error(message || `Failed to load solver options: ${response.statusText}`);
  }

  const parsed = SolverOptionsSchema.safeParse(await response.json());
  if (!parsed.success) {
    throw new Error("Invalid solver options response from backend API");
  }

  const units = parsed.data.planning_units
    .map((unit) => ({
      unitId: unit.planning_unit_id,
      months: monthYear ? [monthYear] : [],
    }))
    .sort((a, b) => a.unitId - b.unitId);

  return { units };
}

export async function listAvailableCaseIdsForMonthAction(monthYear: string): Promise<number[]> {
  try {
    const { units } = await refreshCasesFromSolverOptionsAction(monthYear);
    return units.map((unit) => unit.unitId);
  } catch {
    const { units } = await listCasesAction();
    return units
      .filter((unit) => unit.months.includes(monthYear))
      .map((unit) => unit.unitId)
      .sort((a, b) => a - b);
  }
}
