import { getSolverApiConfig } from "@/lib/config/app-config";
import { Template, TemplateType } from "@/entities/models/template.model";

export interface TemplateDatabase {
  templates: Template<unknown>[];
}

export async function getTemplateDb(caseId: number, templateType: TemplateType) {
  const url = new URL(`${getSolverApiConfig().baseUrl}/templates/${templateType}`);

  url.searchParams.set("planning_unit", String(caseId));

  const response = await fetch(url, { cache: "no-store" });
  const db = {
    data: response.ok ? ((await response.json()) as TemplateDatabase) : { templates: [] },
    async write() {
      await fetch(url, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ data: db.data }),
      });
    },
  };

  return db;
}
