"use server";

import { revalidatePath } from "next/cache";
import { getInjection } from "@/di/container";
import { MinimalStaffRequirements } from "@/entities/models/minimal-staff.model";
import type { ActionResult } from "@/entities/models/action-result.model";

export async function getMinimalStaffAction(caseId: number, monthYear: string): Promise<MinimalStaffRequirements> {
  const controller = getInjection("IGetMinimalStaffController");
  const result = await controller({ caseId, monthYear });
  if ("error" in result) throw new Error(result.error);
  return result.data;
}

export async function updateMinimalStaffAction(
  caseId: number,
  monthYear: string,
  requirements: MinimalStaffRequirements,
): Promise<ActionResult> {
  const controller = getInjection("IUpdateMinimalStaffController");
  const result = await controller({ caseId, monthYear, data: requirements });
  if ("error" in result) return { success: false, error: result.error };
  revalidatePath("/minimal-staff");
  return { success: true, data: undefined };
}
