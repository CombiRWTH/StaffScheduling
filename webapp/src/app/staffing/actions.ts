"use server";

import { revalidatePath } from "next/cache";
import { previewPattern, putDemand } from "@/lib/api";
import type { DemandRequirement, PatternRequirement } from "@/lib/types";

export async function saveDemand(month: string, stationId: number, requirements: DemandRequirement[]) {
  try {
    await putDemand(month, stationId, requirements);
  } catch (error) {
    return { ok: false as const, error: (error as Error).message };
  }
  revalidatePath("/staffing");
  return { ok: true as const };
}

export async function expandPattern(month: string, stationId: number, cells: PatternRequirement[]) {
  try {
    return { ok: true as const, requirements: (await previewPattern(month, stationId, cells)).requirements };
  } catch (error) {
    return { ok: false as const, error: (error as Error).message };
  }
}
