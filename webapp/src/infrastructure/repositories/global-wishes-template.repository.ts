import { IGlobalWishesTemplateRepository } from "@/application/ports/global-wishes-template.repository";
import {
  GlobalWishesTemplateContent,
  GlobalWishesTemplateMetadata,
  Template,
  TemplateSummary,
} from "@/entities/models/template.model";
import { getTemplateDb } from "@/infrastructure/persistence/lowdb/template.db";

export class GlobalWishesTemplateRepositoryAdapter implements IGlobalWishesTemplateRepository {
  async list(caseId: number): Promise<TemplateSummary[]> {
    const db = await getTemplateDb(caseId, "global-wishes");
    return db.data.templates
      .map((t) => ({
        id: t._metadata.id,
        description: t._metadata.description,
        last_modified: t._metadata.last_modified,
        type: "global-wishes" as const,
        fileName: "global-wishes.json",
      }))
      .sort((a, b) => new Date(b.last_modified).getTime() - new Date(a.last_modified).getTime());
  }

  async get(caseId: number, templateId: string): Promise<Template<GlobalWishesTemplateContent>> {
    const db = await getTemplateDb(caseId, "global-wishes");
    const template = db.data.templates.find((t) => t._metadata.id === templateId);
    if (!template) {
      throw new Error(`Global wishes template ${templateId} not found`);
    }
    return template as Template<GlobalWishesTemplateContent>;
  }

  async create(caseId: number, content: GlobalWishesTemplateContent, description: string): Promise<TemplateSummary> {
    const db = await getTemplateDb(caseId, "global-wishes");
    const metadata: GlobalWishesTemplateMetadata = {
      id: Date.now().toString(),
      description,
      last_modified: new Date().toISOString(),
      employeeCount: content.employees.length,
      employeeIds: content.employees.map((e) => e.key),
    };
    db.data.templates.push({ content, _metadata: metadata });
    await db.write();
    return {
      id: metadata.id,
      description: metadata.description,
      last_modified: metadata.last_modified,
      type: "global-wishes",
      fileName: "global-wishes.json",
    };
  }

  async update(
    caseId: number,
    templateId: string,
    data: { content?: GlobalWishesTemplateContent; description?: string },
  ): Promise<Template<GlobalWishesTemplateContent>> {
    const db = await getTemplateDb(caseId, "global-wishes");
    const idx = db.data.templates.findIndex((t) => t._metadata.id === templateId);
    if (idx === -1) {
      throw new Error(`Global wishes template ${templateId} not found`);
    }
    const existing = db.data.templates[idx];
    const newContent = (data.content ?? existing.content) as GlobalWishesTemplateContent;
    const newMetadata: GlobalWishesTemplateMetadata = {
      ...existing._metadata,
      description: data.description ?? existing._metadata.description,
      last_modified: new Date().toISOString(),
      employeeCount: newContent.employees.length,
      employeeIds: newContent.employees.map((e) => e.key),
    };
    db.data.templates[idx] = { content: newContent, _metadata: newMetadata };
    await db.write();
    return db.data.templates[idx] as Template<GlobalWishesTemplateContent>;
  }

  async delete(caseId: number, templateId: string): Promise<void> {
    const db = await getTemplateDb(caseId, "global-wishes");
    db.data.templates = db.data.templates.filter((t) => t._metadata.id !== templateId);
    await db.write();
  }
}
