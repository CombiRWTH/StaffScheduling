import type { IUpdateMinimalStaffTemplateUseCase } from "@/application/use-cases/templates/minimal-staff/update-minimal-staff-template.use-case";
import type { Template } from "@/entities/models/template.model";
import type { MinimalStaffRequirements } from "@/entities/models/minimal-staff.model";
import { isDomainError } from "@/entities/errors/base.errors";

export interface IUpdateMinimalStaffTemplateController {
  (input: {
    caseId: number;
    templateId: string;
    data: { content?: MinimalStaffRequirements; description?: string };
  }): Promise<{ data: Template<MinimalStaffRequirements> } | { error: string }>;
}

export function makeUpdateMinimalStaffTemplateController(
  updateMinimalStaffTemplateUseCase: IUpdateMinimalStaffTemplateUseCase,
): IUpdateMinimalStaffTemplateController {
  return async ({ caseId, templateId, data }) => {
    try {
      const template = await updateMinimalStaffTemplateUseCase({ caseId, templateId, data });
      return { data: template };
    } catch (error) {
      if (isDomainError(error)) return { error: error.message };
      throw error;
    }
  };
}
