"use server";

import { revalidatePath } from "next/cache";
import { getInjection } from "@/di/container";
import { Weights } from "@/entities/models/weights.model";
import type { ActionResult } from "@/entities/models/action-result.model";

export async function getWeightsAction(caseId: number, monthYear: string): Promise<Weights> {
  const controller = getInjection("IGetWeightsController");
  const result = await controller({ caseId, monthYear });
  if ("error" in result) throw new Error(result.error);
  return result.data;
}

export async function updateWeightsAction(caseId: number, monthYear: string, weights: Weights): Promise<ActionResult> {
  const controller = getInjection("IUpdateWeightsController");
  const result = await controller({ caseId, monthYear, weights });
  if ("error" in result) return { success: false, error: result.error };
  revalidatePath("/weights");
  return { success: true, data: undefined };
}
