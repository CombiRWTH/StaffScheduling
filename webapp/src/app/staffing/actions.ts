"use server";

import { previewPattern, putDemand } from "@/lib/api";
import type { DemandCell, PatternRequirement } from "@/lib/types";
import { writeResult } from "@/lib/write-result";

export async function saveDemand(month: string, stationId: number, cells: DemandCell[]) {
  return writeResult(() => putDemand(month, stationId, cells), "/staffing");
}

/** The month's cells for a weekly pattern, computed by the backend; nothing is saved. */
export async function expandPattern(month: string, stationId: number, pattern: PatternRequirement[]) {
  try {
    return { ok: true as const, cells: (await previewPattern(month, stationId, pattern)).cells };
  } catch (error) {
    return { ok: false as const, error: (error as Error).message };
  }
}
