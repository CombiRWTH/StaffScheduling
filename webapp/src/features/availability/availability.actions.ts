"use server";

import { revalidatePath } from "next/cache";
import { getInjection } from "@/di/container";
import { validateMonthYear } from "@/entities/validation/input-validators";
import type { ActionResult } from "@/entities/models/action-result.model";
import type { AvailabilityEmployee } from "@/entities/models/availability.model";
import { getAvailabilityDb } from "@/infrastructure/persistence/lowdb/availability.db";
import { getGlobalAvailabilityDb } from "@/infrastructure/persistence/lowdb/global-availability.db";
import { getAvailabilityTemplateAction } from "@/features/templates/availability-templates.actions";

export async function getAllAvailabilityAction(caseId: number, monthYear: string): Promise<AvailabilityEmployee[]> {
  const controller = getInjection("IGetAllAvailabilityController");
  const result = await controller({ caseId, monthYear });
  if ("error" in result) throw new Error(result.error);
  return result.data;
}

export async function getAvailabilityByKeyAction(
  caseId: number,
  monthYear: string,
  key: number,
): Promise<AvailabilityEmployee | null> {
  const controller = getInjection("IGetAvailabilityByKeyController");
  const result = await controller({ caseId, monthYear, key });
  if ("error" in result) return null;
  return result.data;
}

export async function createAvailabilityAction(
  caseId: number,
  monthYear: string,
  data: AvailabilityEmployee,
): Promise<ActionResult> {
  const controller = getInjection("ICreateAvailabilityController");
  const result = await controller({ caseId, monthYear, entry: data });
  if ("error" in result) return { success: false, error: result.error };
  revalidatePath("/availability");
  return { success: true, data: undefined };
}

export async function updateAvailabilityAction(
  caseId: number,
  monthYear: string,
  key: number,
  data: Partial<Omit<AvailabilityEmployee, "key">>,
): Promise<ActionResult> {
  const controller = getInjection("IUpdateAvailabilityController");
  const result = await controller({ caseId, monthYear, key, data });
  if ("error" in result) return { success: false, error: result.error };
  revalidatePath("/availability");
  return { success: true, data: undefined };
}

export async function deleteAvailabilityAction(caseId: number, monthYear: string, key: number): Promise<ActionResult> {
  const controller = getInjection("IDeleteAvailabilityController");
  const result = await controller({ caseId, monthYear, key });
  if ("error" in result) return { success: false, error: result.error };
  revalidatePath("/availability");
  return { success: true, data: undefined };
}

export async function getAllGlobalAvailabilityAction(
  caseId: number,
  monthYear: string,
): Promise<AvailabilityEmployee[]> {
  const controller = getInjection("IGetAllGlobalAvailabilityController");
  const result = await controller({ caseId, monthYear });
  if ("error" in result) throw new Error(result.error);
  return result.data;
}

export async function getGlobalAvailabilityByKeyAction(
  caseId: number,
  monthYear: string,
  key: number,
): Promise<AvailabilityEmployee | null> {
  const controller = getInjection("IGetGlobalAvailabilityByKeyController");
  const result = await controller({ caseId, monthYear, key });
  if ("error" in result) return null;
  return result.data;
}

export async function createGlobalAvailabilityAction(
  caseId: number,
  monthYear: string,
  data: AvailabilityEmployee,
): Promise<ActionResult> {
  const controller = getInjection("ICreateGlobalAvailabilityController");
  const result = await controller({ caseId, monthYear, entry: data });
  if ("error" in result) return { success: false, error: result.error };
  revalidatePath("/global-availability");
  revalidatePath("/availability");
  return { success: true, data: undefined };
}

export async function updateGlobalAvailabilityAction(
  caseId: number,
  monthYear: string,
  key: number,
  data: Partial<Omit<AvailabilityEmployee, "key">>,
): Promise<ActionResult> {
  const controller = getInjection("IUpdateGlobalAvailabilityController");
  const result = await controller({ caseId, monthYear, key, data });
  if ("error" in result) return { success: false, error: result.error };
  revalidatePath("/global-availability");
  revalidatePath("/availability");
  return { success: true, data: undefined };
}

export async function deleteGlobalAvailabilityAction(
  caseId: number,
  monthYear: string,
  key: number,
): Promise<ActionResult> {
  const controller = getInjection("IDeleteGlobalAvailabilityController");
  const result = await controller({ caseId, monthYear, key });
  if ("error" in result) return { success: false, error: result.error };
  revalidatePath("/global-availability");
  revalidatePath("/availability");
  return { success: true, data: undefined };
}

export async function importAvailabilityTemplateAction(
  caseId: number,
  monthYear: string,
  templateId: string,
): Promise<ActionResult<{ importedCount: number }>> {
  try {
    validateMonthYear(monthYear);
    const templateResult = await getAvailabilityTemplateAction(caseId, templateId);
    if (!templateResult.success) return templateResult;

    const globalDb = await getGlobalAvailabilityDb(caseId, monthYear);
    const monthlyDb = await getAvailabilityDb(caseId, monthYear);
    const globalEmployees = templateResult.data.content.employees;
    const globalController = getInjection("ICreateGlobalAvailabilityController");

    globalDb.data.employees = [];
    monthlyDb.data.employees = [];
    await globalDb.write();
    await monthlyDb.write();

    for (const employee of globalEmployees) {
      const result = await globalController({ caseId, monthYear, entry: employee });
      if ("error" in result) return { success: false, error: result.error };
    }

    revalidatePath("/global-availability");
    revalidatePath("/availability");
    return { success: true, data: { importedCount: globalEmployees.length } };
  } catch (error) {
    return { success: false, error: error instanceof Error ? error.message : String(error) };
  }
}
