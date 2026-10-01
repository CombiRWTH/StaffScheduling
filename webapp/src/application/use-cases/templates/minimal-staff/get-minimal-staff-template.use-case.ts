import { IMinimalStaffTemplateRepository } from "@/application/ports/minimal-staff-template.repository";
import { Template } from "@/entities/models/template.model";
import { MinimalStaffRequirements } from "@/entities/models/minimal-staff.model";
import { TemplateNotFoundError } from "@/entities/errors/template.errors";

export interface IGetMinimalStaffTemplateUseCase {
  (input: { caseId: number; templateId: string }): Promise<Template<MinimalStaffRequirements>>;
}

export function makeGetMinimalStaffTemplateUseCase(
  repository: IMinimalStaffTemplateRepository,
): IGetMinimalStaffTemplateUseCase {
  return async ({ caseId, templateId }) => {
    try {
      return await repository.get(caseId, templateId);
    } catch {
      throw new TemplateNotFoundError(templateId);
    }
  };
}
