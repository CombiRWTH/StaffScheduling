"use server";

import { revalidatePath } from "next/cache";
import type {
  AvailabilityTemplateContent,
  AvailabilityTemplateMetadata,
  Template,
  TemplateSummary,
} from "@/entities/models/template.model";
import type { ActionResult } from "@/entities/models/action-result.model";
import { getTemplateDb } from "@/infrastructure/persistence/lowdb/template.db";

const TEMPLATE_TYPE = "availability" as const;
const FILE_NAME = "availability.json";

function toSummary(template: Template<unknown>): TemplateSummary {
  return {
    id: template._metadata.id,
    description: template._metadata.description,
    last_modified: template._metadata.last_modified,
    type: TEMPLATE_TYPE,
    fileName: FILE_NAME,
  };
}

export async function listAvailabilityTemplatesAction(caseId: number): Promise<TemplateSummary[]> {
  const db = await getTemplateDb(caseId, TEMPLATE_TYPE);
  return db.data.templates
    .map(toSummary)
    .sort((a, b) => new Date(b.last_modified).getTime() - new Date(a.last_modified).getTime());
}

export async function getAvailabilityTemplateAction(
  caseId: number,
  templateId: string,
): Promise<ActionResult<Template<AvailabilityTemplateContent>>> {
  try {
    const db = await getTemplateDb(caseId, TEMPLATE_TYPE);
    const template = db.data.templates.find((item) => item._metadata.id === templateId);
    if (!template) return { success: false, error: `Availability template ${templateId} not found` };
    return { success: true, data: template as Template<AvailabilityTemplateContent> };
  } catch (error) {
    return { success: false, error: error instanceof Error ? error.message : String(error) };
  }
}

export async function createAvailabilityTemplateAction(
  caseId: number,
  content: AvailabilityTemplateContent,
  description: string,
): Promise<ActionResult<TemplateSummary>> {
  try {
    const db = await getTemplateDb(caseId, TEMPLATE_TYPE);
    const metadata: AvailabilityTemplateMetadata = {
      id: Date.now().toString(),
      description,
      last_modified: new Date().toISOString(),
      employeeCount: content.employees.length,
      employeeIds: content.employees.map((employee) => employee.key),
    };
    const template: Template<AvailabilityTemplateContent> = { content, _metadata: metadata };
    db.data.templates.push(template);
    await db.write();
    revalidatePath("/templates/availability");
    revalidatePath("/global-availability");
    return { success: true, data: toSummary(template) };
  } catch (error) {
    return { success: false, error: error instanceof Error ? error.message : String(error) };
  }
}

export async function updateAvailabilityTemplateAction(
  caseId: number,
  templateId: string,
  data: { content?: AvailabilityTemplateContent; description?: string },
): Promise<ActionResult<Template<AvailabilityTemplateContent>>> {
  try {
    const db = await getTemplateDb(caseId, TEMPLATE_TYPE);
    const index = db.data.templates.findIndex((item) => item._metadata.id === templateId);
    if (index === -1) return { success: false, error: `Availability template ${templateId} not found` };

    const existing = db.data.templates[index];
    const content = (data.content ?? existing.content) as AvailabilityTemplateContent;
    const metadata: AvailabilityTemplateMetadata = {
      ...existing._metadata,
      description: data.description ?? existing._metadata.description,
      last_modified: new Date().toISOString(),
      employeeCount: content.employees.length,
      employeeIds: content.employees.map((employee) => employee.key),
    };
    db.data.templates[index] = { content, _metadata: metadata };
    await db.write();
    revalidatePath("/templates/availability");
    return { success: true, data: db.data.templates[index] as Template<AvailabilityTemplateContent> };
  } catch (error) {
    return { success: false, error: error instanceof Error ? error.message : String(error) };
  }
}

export async function deleteAvailabilityTemplateAction(caseId: number, templateId: string): Promise<ActionResult> {
  try {
    const db = await getTemplateDb(caseId, TEMPLATE_TYPE);
    db.data.templates = db.data.templates.filter((item) => item._metadata.id !== templateId);
    await db.write();
    revalidatePath("/templates/availability");
    return { success: true, data: undefined };
  } catch (error) {
    return { success: false, error: error instanceof Error ? error.message : String(error) };
  }
}
