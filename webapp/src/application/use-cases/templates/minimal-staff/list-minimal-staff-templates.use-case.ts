import { IMinimalStaffTemplateRepository } from "@/application/ports/minimal-staff-template.repository";
import { TemplateSummary } from "@/entities/models/template.model";

export interface IListMinimalStaffTemplatesUseCase {
  (input: { caseId: number }): Promise<TemplateSummary[]>;
}

export function makeListMinimalStaffTemplatesUseCase(
  repository: IMinimalStaffTemplateRepository,
): IListMinimalStaffTemplatesUseCase {
  return async ({ caseId }) => {
    return repository.list(caseId);
  };
}
