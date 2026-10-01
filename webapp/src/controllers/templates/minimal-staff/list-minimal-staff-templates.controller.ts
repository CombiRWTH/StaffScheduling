import type { IListMinimalStaffTemplatesUseCase } from "@/application/use-cases/templates/minimal-staff/list-minimal-staff-templates.use-case";
import type { TemplateSummary } from "@/entities/models/template.model";
import { isDomainError } from "@/entities/errors/base.errors";

export interface IListMinimalStaffTemplatesController {
  (input: { caseId: number }): Promise<{ data: TemplateSummary[] } | { error: string }>;
}

export function makeListMinimalStaffTemplatesController(
  listMinimalStaffTemplatesUseCase: IListMinimalStaffTemplatesUseCase,
): IListMinimalStaffTemplatesController {
  return async ({ caseId }) => {
    try {
      const templates = await listMinimalStaffTemplatesUseCase({ caseId });
      return { data: templates };
    } catch (error) {
      if (isDomainError(error)) return { error: error.message };
      throw error;
    }
  };
}
