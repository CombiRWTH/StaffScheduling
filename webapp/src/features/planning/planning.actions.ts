"use server";
import { monthParams, readPlanningApi } from "./api";
import { PlanningOptionsSchema } from "./models";

export async function loadPlanningOptions(month: string) {
  try {
    return { data: await readPlanningApi("/planning/options", monthParams(month), PlanningOptionsSchema) };
  } catch (error) {
    return { error: error instanceof Error ? error.message : "Planungsauswahl nicht verfügbar." };
  }
}
