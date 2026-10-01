import type { IDeleteWeightsTemplateUseCase } from "@/application/use-cases/templates/weights/delete-weights-template.use-case";
import { isDomainError } from "@/entities/errors/base.errors";

export interface IDeleteWeightsTemplateController {
  (input: { caseId: number; templateId: string }): Promise<{ data: { success: boolean } } | { error: string }>;
}

export function makeDeleteWeightsTemplateController(
  deleteWeightsTemplateUseCase: IDeleteWeightsTemplateUseCase,
): IDeleteWeightsTemplateController {
  return async ({ caseId, templateId }) => {
    try {
      await deleteWeightsTemplateUseCase({ caseId, templateId });
      return { data: { success: true } };
    } catch (error) {
      if (isDomainError(error)) return { error: error.message };
      throw error;
    }
  };
}
