import type { IDeleteMinimalStaffTemplateUseCase } from "@/application/use-cases/templates/minimal-staff/delete-minimal-staff-template.use-case";
import { isDomainError } from "@/entities/errors/base.errors";

export interface IDeleteMinimalStaffTemplateController {
  (input: { caseId: number; templateId: string }): Promise<{ data: { success: boolean } } | { error: string }>;
}

export function makeDeleteMinimalStaffTemplateController(
  deleteMinimalStaffTemplateUseCase: IDeleteMinimalStaffTemplateUseCase,
): IDeleteMinimalStaffTemplateController {
  return async ({ caseId, templateId }) => {
    try {
      await deleteMinimalStaffTemplateUseCase({ caseId, templateId });
      return { data: { success: true } };
    } catch (error) {
      if (isDomainError(error)) return { error: error.message };
      throw error;
    }
  };
}
