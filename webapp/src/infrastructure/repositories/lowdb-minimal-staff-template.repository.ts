import { IMinimalStaffTemplateRepository } from "@/application/ports/minimal-staff-template.repository";
import { Template, TemplateMetadata, TemplateSummary } from "@/entities/models/template.model";
import { MinimalStaffRequirements } from "@/entities/models/minimal-staff.model";
import { getTemplateDb } from "@/infrastructure/persistence/lowdb/template.db";

export class LowdbMinimalStaffTemplateRepository implements IMinimalStaffTemplateRepository {
  async list(caseId: number): Promise<TemplateSummary[]> {
    const db = await getTemplateDb(caseId, "minimal-staff");
    return db.data.templates
      .map((t) => ({
        id: t._metadata.id,
        description: t._metadata.description,
        last_modified: t._metadata.last_modified,
        type: "minimal-staff" as const,
        fileName: "minimal-staff.json",
      }))
      .sort((a, b) => new Date(b.last_modified).getTime() - new Date(a.last_modified).getTime());
  }

  async get(caseId: number, templateId: string): Promise<Template<MinimalStaffRequirements>> {
    const db = await getTemplateDb(caseId, "minimal-staff");
    const template = db.data.templates.find((t) => t._metadata.id === templateId);
    if (!template) {
      throw new Error(`Minimal-staff template ${templateId} not found`);
    }
    return template as Template<MinimalStaffRequirements>;
  }

  async create(caseId: number, content: MinimalStaffRequirements, description: string): Promise<TemplateSummary> {
    const db = await getTemplateDb(caseId, "minimal-staff");
    const metadata: TemplateMetadata = {
      id: Date.now().toString(),
      description,
      last_modified: new Date().toISOString(),
    };
    db.data.templates.push({ content, _metadata: metadata });
    await db.write();
    return {
      id: metadata.id,
      description: metadata.description,
      last_modified: metadata.last_modified,
      type: "minimal-staff",
      fileName: "minimal-staff.json",
    };
  }

  async update(
    caseId: number,
    templateId: string,
    data: { content?: MinimalStaffRequirements; description?: string },
  ): Promise<Template<MinimalStaffRequirements>> {
    const db = await getTemplateDb(caseId, "minimal-staff");
    const idx = db.data.templates.findIndex((t) => t._metadata.id === templateId);
    if (idx === -1) {
      throw new Error(`Minimal-staff template ${templateId} not found`);
    }
    const existing = db.data.templates[idx];
    db.data.templates[idx] = {
      content: data.content ?? existing.content,
      _metadata: {
        ...existing._metadata,
        description: data.description ?? existing._metadata.description,
        last_modified: new Date().toISOString(),
      },
    };
    await db.write();
    return db.data.templates[idx] as Template<MinimalStaffRequirements>;
  }

  async delete(caseId: number, templateId: string): Promise<void> {
    const db = await getTemplateDb(caseId, "minimal-staff");
    db.data.templates = db.data.templates.filter((t) => t._metadata.id !== templateId);
    await db.write();
  }
}
